import logging
from contextlib import asynccontextmanager
from datetime import datetime

import asyncio
import telethon
from sqlalchemy import Column, Integer, String, UniqueConstraint, BigInteger, select, Date
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.pool import NullPool
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputPeerUser, InputPeerChannel

from tg_config import CONFIG
from tg_log import print_d, print_e

conf = CONFIG["tg_db"]

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)


engine = create_async_engine(
        conf['DATABASE_URL_ASYNC'],
        echo=False,
        poolclass=NullPool
    )

SessionLocal = async_sessionmaker(
    class_=AsyncSession,
    bind=engine,
    expire_on_commit=False,
    autoflush=False
)


@asynccontextmanager
async def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()

Base = declarative_base()

class Author(Base):
    __tablename__ = 'author'
    id = Column(BigInteger, primary_key=True)
    f_name = Column(String(255), nullable=True)
    l_name = Column(String(64), nullable=True)

    messages = relationship('Msg', backref='author')

async def get_sender(session, client, user_id:int):
    if user_id is None:
        return None
    sender = await client.get_input_entity(user_id)
    author_id = None

    if isinstance(sender, InputPeerUser):
        author_id = sender.user_id
        result = await session.execute(select(Author).where(Author.id == author_id))
        author = result.scalars().first()

        if author is None and sender.user_id is not None:
            try:
                user = await client(GetFullUserRequest(sender))
            except telethon.errors.rpcerrorlist.ChannelPrivateError:
                print_e(f"ChannelPrivateError: {sender.user_id}")
                return None
            user_full = user.full_user
            print_d(f"Added user with name: {user_full.private_forward_name}")
            first_name, last_name = None, None
            if user_full.private_forward_name is not None:
                first_name = user_full.private_forward_name.rsplit(" ", 1)[0]
                last_name = user_full.private_forward_name.split(" ")[-1]
            author = Author(id=user_full.id, f_name=first_name, l_name=last_name)
            session.add(author)
            await session.commit()
    elif isinstance(sender, InputPeerChannel):
        author_id = sender.channel_id
        result = await session.execute(select(Author).where(Author.id == author_id))
        author = result.scalars().first()

        if author is None:
            channel = await client(GetFullChannelRequest(sender))
            author = Author(id=channel.full_chat.id, f_name=channel.full_chat.about, l_name="")
            session.add(author)
            await session.commit()

    return author_id

class Channel(Base):
    __tablename__ = 'channel'
    name = Column(String, primary_key=True)
    description = Column(String(512), nullable=True)
    last_seen = Column(DateTime, nullable=True)

    offset_id = Column(Integer, nullable=True)

    messages = relationship('Msg', backref='channel')

async def get_channel(session: AsyncSession, name: str) -> Channel:
    channel = (await session.execute(
        select(Channel).where(Channel.name == name)
    )).scalars().first()

    if channel is None:
        channel = Channel(name=name)
        session.add(channel)
        await session.commit()
        await session.refresh(channel)

    return channel

class Msg(Base):
    __tablename__ = 'msg'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_order = Column(Integer, nullable=False)
    send_date = Column(Date, nullable=True)
    save_date = Column(Date, nullable=True)
    content= Column(String(4096), nullable=True)
    #TODO get links to file to extra table
    file = Column(String, nullable=True)
    reply_to = Column(Integer, ForeignKey('msg.id'))

    author_id = Column(BigInteger, ForeignKey('author.id'))
    channel_name = Column(String(255), ForeignKey('channel.name'))
    replies = relationship('Msg', backref=backref('parent', remote_side=[id]))
    __table_args__ = (UniqueConstraint('tg_order', 'channel_name', name='_tg_order_channel_uc'),)

author_cache = {}
async def insert_message(session, message, client, channel_name, file_names_str):

    #cache by sender_id to not get another requests
    sender_id = author_cache.get(message.sender_id)
    if sender_id is None:
        sender_id = await get_sender(session, client, message.sender_id)
        author_cache[message.sender_id] = sender_id

    msg = insert(Msg).values(
        tg_order=message.id,
        send_date=datetime.fromisoformat(str(message.date)),
        save_date=datetime.now(),
        author_id=sender_id,
        content=message.message,
        channel_name=channel_name,
        file=file_names_str
    ).on_conflict_do_nothing(index_elements=['tg_order', 'channel_name'])

    result = await session.execute(msg)

    if result.inserted_primary_key is not None:
        print_d(f"+ msg {message.id}", end=" -> ")
        return result.inserted_primary_key[0]
    else:
        existing_msg = await session.execute(
            select(Msg.id).where(Msg.tg_order == message.id, Msg.channel_name == channel_name)
        )
        existing_msg_id = existing_msg.scalar_one_or_none()
        if existing_msg_id is not None:
            print_e(f"Message {message.id} already exists with ID {existing_msg_id}")
            return existing_msg_id
        else:
            print_e(f"No existing message found for {message.id}")
            return None

async def insert_replies(session, replies):
    reply_msgs = insert(Msg).values(replies).on_conflict_do_nothing(index_elements=['tg_order', 'channel_name'])
    await session.execute(reply_msgs)
    #print_d(f"Inserted {len(replies)} replies")

async def delete_message(session, message_id):
    msg = await session.execute(select(Msg).where(Msg.id == message_id))
    message = msg.scalars().first()
    if message is not None:
        await session.delete(message)
        await session.commit()

class Regex(Base):
    __tablename__ = 'regex'
    content = Column(String)
    name = Column(String, nullable=False,primary_key=True)
    __table_args__ = (UniqueConstraint('content', 'name', name='_content_name'),)

async def get_regexes(session, regex_names):
    regexes = []
    for name in regex_names:
        result = await session.execute(select(Regex).where(Regex.name == name))
        regex = result.scalars().first()
        if regex is not None:
            regexes.append(regex.content)
    return regexes

async def add_regexes(regexes):
    async with get_session() as session:
        for name, pattern in regexes.items():
            reg = insert(Regex).values(
                name=name, content=pattern
            ).on_conflict_do_nothing(index_elements=['content','name'])
            await session.execute(reg)

async def create_tables(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def update_offset(session, channel_name ,offset_id):
    channel = await get_channel(session, channel_name)
    channel.offset_id = offset_id
    await session.commit()

asyncio.run(create_tables(engine))
default_regexes = CONFIG['default_regexes']
asyncio.run(add_regexes(default_regexes))

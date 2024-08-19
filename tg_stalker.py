#only one script can run at a time
import asyncio
import json
import os
import re
import sys
import traceback
from datetime import datetime
from functools import lru_cache
from typing import Any

import telethon
from discord_webhook import DiscordWebhook
from input_parser import input_parser
import lockfile
from telethon import functions, TelegramClient
from telethon.errors import ChannelInvalidError, ChannelPrivateError, InputUserDeactivatedError, PeerIdInvalidError, \
    MsgIdInvalidError
from telethon.tl.functions.messages import GetHistoryRequest
from tg_config import CONFIG
from tg_log import print_d, print_e, print_ok

conf = CONFIG['tg_stalker']

def print_to_discord(msg="msg not set", ping=False, users=conf['DEFAULT_USERS'], std=False):
    if not conf['DISCORD']:
        return
    if std:
        print(msg)
    if ping and users:
        msg = " ".join([f"<@{user_id}>" for user_id in users]) + f" {msg}"
    try:
        DiscordWebhook(url=conf['WEBHOOK'], content=msg).execute()
    except Exception as e:
        print_e(f"Discord error {e.__class__.__name__}")



def get_args():
    parser = input_parser.InputParser()

    parser.add_argument("--save_new",
                        input="Save? ",
                        action="store_true",
                        help="Save new messages from channels in CHANNEL_SAVE_ALL"
                        )
    parser.add_argument("--stalk_regex",
                        input="Stalk with regex? ",
                        action="store_true",
                        help="Stalk with regex channel in CHANNEL_STALK_REGEX"
                        )

    args = parser.parse_args()
    print_e("\nFull Command: ")
    print_e(parser.str_command(args))
    return args

@lru_cache(maxsize=128)
def get_compiled_regex(regex):
    return re.compile(regex, re.IGNORECASE | re.DOTALL)

def regex_check(regex_list, message, echo=False, prefix=""):
    if not regex_list:
        return True
    if not message:
        return False
    for regex in regex_list:
        if get_compiled_regex(regex).search(message):
            if echo:
                print_to_discord(prefix + message, ping=True)
            return True
    return False

async def get_peer(client, channel_name):
    peer = None
    try:
         peer = await client.get_input_entity(channel_name)
    except PeerIdInvalidError:
        print_e(f"Invalid channel name: {channel_name}")
    except (ChannelInvalidError, ChannelPrivateError, InputUserDeactivatedError) as e:
        print_e(f"Error retrieving entity for channel {channel_name}: {e}")
    except Exception as e:
        print_e(f"Unexpected error: {e}")
        print_to_discord(f"Unexpected error: {e}")
    finally:
        return peer

async def get_messages(client, offset_id: int, channel_name):

    peer = await get_peer(client, channel_name)
    if peer is None:
        return []
    history = await client(GetHistoryRequest(
        peer=peer,
        offset_id=offset_id,
        offset_date=None,
        add_offset=0,
        limit=100,
        max_id=0,
        min_id=0,
        hash=0
    ))
    if not history.messages:
        print_e(f"End of history")
        return None
    return history.messages


async def get_all_replies(channel_name, message, client):
    offset_id = 0
    all_replies = []
    peer = await get_peer(client, channel_name)
    if peer is None:
        return []
    while True:
        try:
            replies = await client(functions.messages.GetRepliesRequest(
                peer=peer,
                msg_id=message.id,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            all_replies.extend(replies.messages)
            if len(replies.messages) < 100:
                break
            offset_id = replies.messages[-1].id
        except PeerIdInvalidError:
            print_e(f"Invalid peer used in GetRepliesRequest for channel: {channel_name}")
            break
        except MsgIdInvalidError:
            #print_e(f"Invalid message id used in GetRepliesRequest for channel: {channel_name}")
            break
        except Exception as e:
            print_e(f"Unexpected error while fetching replies: {e.__class__.__name__} {e} {message.id}")
            break
    return all_replies

async def save_replies(session, client, channel_name, message=None, regex_list=None,
                       msg_saved=False, inserted_id=None, stats=None):
    if regex_list is None:
        regex_list = []
    if not conf['ignore_replies']:
        try:

            replies = await get_all_replies(channel_name, message, client)
            #print_d(f"Loaded {len(replies)} replies for {message.id}")

            replies_for_save = []
            author_ids = {}

            for reply in replies:
                match = regex_check(regex_list, reply.message, echo=True, prefix=f"{channel_name} reply:")
                if regex_list is None or (msg_saved and conf['regex_all_comments']) or match:
                    if inserted_id == -1:
                        inserted_id = await insert_message(session, message, client, channel_name)
                    if reply.sender_id not in author_ids:
                        author_ids[reply.sender_id] = await get_sender(session, client, reply.sender_id)
                    replies_for_save.append({
                        'tg_order': reply.id,
                        'send_date': str(reply.date),
                        'save_date': str(datetime.now()),
                        'author_id': author_ids[reply.sender_id],
                        'content': reply.message,
                        'channel_name': channel_name,
                        'reply_to': inserted_id
                    })
                    stats['replies_c'] += 1

            if replies_for_save: # Insert all replies in one batch
                await insert_replies(session, replies_for_save)
        except MsgIdInvalidError: # no replies ?
            print_to_discord(f"MsgIdInvalidError {message.id}")
        except Exception as e:
            print_e(f"comments Error  {type(e).__name__}")
            traceback.print_exc()


async def tg_download(message, regex_list, prefix=""):
    if (conf['download_regex_files'] and message.file and
            regex_check(regex_list, message.file.name, echo=True, prefix=prefix)):
        await message.download_media(file="./downloads/")
        return True
    return False

run_stats = {"replies_c": 0,'message_c':0, "msg_insert": 0}
async def save_all_after(session, client, channel_name, last_seen, max_history=conf['max_requests'], offset_id=0, regex_list=None)-> bool | tuple[bool, Any]:

    stats = {"replies_c": 0,'message_c':0, "msg_insert": 0}
    try:
        first_msg_date = None
        for req_count, _ in enumerate(range(max_history)):
            #save messages
            messages = await get_messages(client,offset_id, channel_name)
            if messages is None or messages is []:
                return True, None
            if first_msg_date is None:
                first_msg_date = messages[0].date.replace(tzinfo=None)
            stats['message_c'] += len(messages)
            print_d(f"loaded {len(messages)} msgs", end=" -> ")

            old_offset_id = offset_id
            for message in messages:

                #Check if already end by date
                if last_seen is not None and message.date.replace(tzinfo=None) <= last_seen:
                    print_d(f"last is from {message.date.replace(tzinfo=None)}(it is before {last_seen})", end=" -> ")
                    return True, first_msg_date

                msg_saved = False

                #get file name in json
                file_names = []
                # Check if message.file is a list (or any iterable other than a string)
                if isinstance(message.file, (list, tuple, set)):
                    for file in message.file:
                        if file.name is not None:
                            file_names.append(file.name)
                # Check if message.file is a single object with a 'name' attribute
                elif message.file is not None and hasattr(message.file, 'name') and message.file.name is not None:
                    file_names.append(message.file.name)

                file_names_str = str(json.dumps(file_names, ensure_ascii=False))
                if file_names_str == "[]":
                    file_names_str=None

                file_name = (file_names_str is not None and regex_check(regex_list, file_names_str, echo=True, prefix=f"{channel_name} :"))
                await tg_download(message, regex_list, prefix=f"{channel_name}:")

                inserted_id = -1
                if regex_list is None or regex_check(regex_list, message.message, echo=True, prefix=f"{channel_name} :") or file_name:
                    inserted_id = await insert_message(session, message, client, channel_name, file_names_str)
                    msg_saved = True
                    stats['msg_insert'] += 1

                await save_replies(session, client, channel_name, message, regex_list, msg_saved=msg_saved, inserted_id=inserted_id, stats=stats)
                await session.commit()
                offset_id = message.id
            if old_offset_id == offset_id:
                print_ok("Offset didnt change")
                return True, first_msg_date
        return True, None #TODO
    except (asyncio.CancelledError, KeyboardInterrupt):
        await session.rollback()
        print_to_discord("KeyboardInterrupt", ping=True)
        keyboard_interrupt_occurred = True
    finally:
        await update_offset(session, channel_name, offset_id)
        print_d(f"offset: {offset_id} - {stats['msg_insert']}/{stats['message_c']} messages, {stats['replies_c']} replies", end=" -> ")
        #save stats into run_stats sum
        for key in stats:
            run_stats[key] += stats[key]

    if keyboard_interrupt_occurred:
        raise KeyboardInterrupt
    return False, None

async def save_channel(client, channel_name: str, only_regex=False):
    async with get_session() as session: #session maker have turned off autofalh, nessasay to commit changes
        channel = await get_channel(session, channel_name)
        compiled_regex_list = None
        if only_regex:
            regex_list = await get_regexes(session, conf['CHANNEL_STALK_REGEX'][channel_name])
            compiled_regex_list = [regex for regex in regex_list]

        offset_id = 0
        if conf['reset'] and channel.offset_id is not None:
            offset_id=channel.offset_id

        success, new_date = await save_all_after(session, client, channel.name, channel.last_seen, regex_list=compiled_regex_list, offset_id=offset_id)
        if success:
            if new_date is None:
                channel.last_seen = new_date
            channel.offset_id = 0
            await session.commit()
            print_ok("saved")

class Stalker:
    def __init__(self):
        self.client = None
        self.queue = asyncio.Queue()

    async def start_client(self):
        self.client = TelegramClient('userbot', conf['API_ID'], conf['API_HASH'])
        print(f"Login: {conf['API_ID']}\n{conf['API_HASH']}\n{conf['PHONE_NUMBER']}")
        # await say WARNING, but it dot works without it
        await self.client.start(phone=conf['PHONE_NUMBER'])

        if await self.client.is_user_authorized():
            print_ok("Client successfully logged in.")
        else:
            print_to_discord("Client login failed.", ping=True)

    async def worker(self, only_regex=False):
        running = True
        while running:
            try:
                channel_name = await self.queue.get()
                print_ok(f"{channel_name} -> ", end="")
                await save_channel(self.client, channel_name, only_regex=only_regex)
                self.queue.task_done()
            except KeyboardInterrupt:
                running = False
                print_e("Waiting for tasks to finish")
            except telethon.errors.rpcerrorlist.ChannelPrivateError as e:
                print_e(f"ChannelPrivateError {e}")
            except Exception as e:
                print_e(f"Error processing task {e}")
                traceback.print_exc()

    #TODO add parallel downloading with multiple clients
    async def scan(self, names=None, max_workers=conf['max_workers'], only_regex=False):
        if names is None:
            names = []
        await self.start_client()

        for channel_name in names:
            await self.queue.put(channel_name)

            workers = [
                asyncio.create_task(self.worker(only_regex=only_regex))
                for _ in range(max_workers)
            ]
            await self.queue.join()

            for worker in workers:
                worker.cancel()
        print_to_discord(f"Run stats: {run_stats['msg_insert']}/{run_stats['message_c']} messages, {run_stats['replies_c']} replies", std=True)

def with_lock(lock_file_path, timeout=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            lock = lockfile.FileLock(lock_file_path)
            try:
                lock.acquire(timeout=timeout)
            except lockfile.LockTimeout:
                print_e("Script is already running. Exiting.")
                print_to_discord("Script is already running. Exiting.", ping=True)
                sys.exit(0)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print_to_discord(f"with_lock error {e}")
            finally:
                lock.release()

        return wrapper
    return decorator

def update_database_url(save_new, stalk_regex):
    if save_new:
        CONFIG["tg_db"]['DATABASE_URL_ASYNC'] = CONFIG["tg_db"]['DATABASE_URL_SAVE_NEW']
    elif stalk_regex:
        CONFIG["tg_db"]['DATABASE_URL_ASYNC'] = CONFIG["tg_db"]['DATABASE_URL_STALK_REGEX']

ARGS = get_args()
update_database_url(ARGS.save_new, ARGS.stalk_regex)
from tg_db import insert_message, get_sender, get_channel, get_session, insert_replies, get_regexes, update_offset

@with_lock(f"/tmp/tg_stalker.lock")
def main():
    print_to_discord("Tg_stalker started")
    try:
        if ARGS.save_new and ARGS.stalk_regex:
            print_e("Only one option can be set")
            sys.exit(1)

        stalker = Stalker()
        if ARGS.save_new:
            names = conf['CHANNEL_SAVE_ALL']
            asyncio.run(stalker.scan(names=names))
            print_to_discord("Tg_stalker save_new checked")
        if ARGS.stalk_regex:
            if conf['download_regex_files']:
                os.makedirs('./downloads', exist_ok=True)
            names = conf['CHANNEL_STALK_REGEX'].keys()
            asyncio.run(stalker.scan(names=names, only_regex=True))
            print_to_discord("Tg_stalker stalk_regex checked")
    except KeyboardInterrupt:
        print_e("\nKeyboardInterrupt")
        sys.exit(1)
    except TimeoutError:
        print_to_discord("\nTimeoutError invalid database connection?", ping=True)
        sys.exit(1)

if __name__ == '__main__':
    main()

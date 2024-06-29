import traceback
import re
import traceback

from discord_webhook import DiscordWebhook
from input_parser import InputParser
from lockfile import FileLock, LockTimeout
from telethon import TelegramClient
from telethon.errors import MsgIdInvalidError

from tg_db import *
from tg_log import *

conf=CONFIG['tg_stalker']
stalker = None

def get_args():
    parser = InputParser()

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
    print("\nFull Command: ")
    print(parser.str_command(args))
    return args

def regex_check(regex_list, message, echo=False):
    if message is None:
        return False
    for regex in regex_list:
        if re.search(regex, message):
            if echo:
                print_to_discord(message, ping=True)
            return True
    return False

def print_to_discord(msg="msg not set", ping=False, users=conf['DEFAULT_USERS'], std=False):
    if not conf['DISCORD']:
        return
    if std:
        print(msg)
    if ping and users:
        for user_id in users:
            msg = f"<@{user_id}> {msg}"
    webhook = DiscordWebhook(url=conf['WEBHOOK'], content=msg)
    webhook.execute()

async def save_all_after(session, client, channel_name, last_seen, max_history=conf['max_requests'], offset_id=conf['offset_id'], regex_list=None):
    req_count = 0
    replies_c, message_c, msg_deleted = 0, 0 ,0
    while req_count < max_history:
        print(f"{req_count=}/{max_history}")
        history = await client(GetHistoryRequest(
            peer=channel_name,
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
            break
        message_c += len(history.messages)
        for message in history.messages:
            if last_seen is not None and message.date.replace(tzinfo=None) <= last_seen:
                return
            save = False

            if message.message is None:
                print_e(f"message is None")
                continue

            if regex_list is None or regex_check(regex_list, message.message, echo=True):
                save = True

            if not conf['ignore_replies'] or save:
                inserted_id = await insert_message(session, message,client, channel_name)
            else:
                msg_deleted += 1

            if not conf['ignore_replies']:
                try:
                    replies = await client(GetRepliesRequest(
                        peer=channel_name,
                        msg_id=message.id,
                        offset_id=0,
                        offset_date=None,
                        add_offset=0,
                        limit=100,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    msg_save=save
                    for reply in replies.messages:
                        match = regex_check(regex_list, reply.message, echo=True)
                        if regex_list is None or (msg_save and conf['regex_all_comments']) or match:
                            save = True
                            await insert_reply(session, reply, client, channel_name, inserted_id)
                            replies_c=+1
                    if not save:
                        await session.rollback()
                        msg_deleted += 1
                except MsgIdInvalidError:
                    pass
                    #print(f"message {message.id} has no replies")
                except Exception as e:
                    print(f"comments Error  {e.__class__.__name__}")
                    traceback.print_exc()

            await session.commit()
        offset_id = history.messages[-1].id
        print(f"{offset_id}\t{message_c-msg_deleted}/{message_c} inserted, {replies_c} replies")
        req_count += 1


async def save_channel(client, channel_name: str, only_regex=False):
    async with get_session() as session:
        channel: Channel = await get_channel(session, channel_name)
        regex_list = None
        if only_regex:
            regex_list = await get_regexes(session, conf['CHANNEL_STALK_REGEX'][channel_name])
        await save_all_after(session, client, channel.name, channel.last_seen, regex_list=regex_list)
        channel.last_seen = datetime.now()
        await session.commit()

class Stalker():
    def __init__(self):
        self.client = None
        self.queue = asyncio.Queue()

    async def start_client(self):
        self.client = TelegramClient('userbot', conf['API_ID'], conf['API_HASH'])
        await self.client.start(phone=conf['PHONE_NUMBER'])

    async def worker(self, only_regex=False):
        while True:
            try:
                channel_name = await self.queue.get()
                print_ok(f"Processing {channel_name}")
                await save_channel(self.client, channel_name, only_regex=only_regex)
                self.queue.task_done()
            except Exception as e:
                print(f"Error processing task {e}")
                traceback.print_exc()

    async def scan(self, names=[], max_workers=conf['max_workers'],only_regex=False):
        global stalker
        await stalker.start_client()
        for channel_name in names:
            await self.queue.put(channel_name)

            workers = [
                asyncio.create_task(self.worker(only_regex=only_regex))
                for _ in range(max_workers)
            ]
            await self.queue.join()

            for worker in workers:
                worker.cancel()


def with_lock(lock_file_path, timeout=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            lock = FileLock(lock_file_path)
            try:
                lock.acquire(timeout=timeout)
            except LockTimeout:
                print("Script is already running. Exiting.")
                print_to_discord("Script is already running. Exiting.", ping=True)
                sys.exit(0)

            try:
                return func(*args, **kwargs)
            finally:
                lock.release()

        return wrapper

    return decorator

@with_lock(f"/tmp/{__name__}.lock")
def main():
    ARGS = get_args()
    # print(ARGS.save_new,type(ARGS.save_new))
    global stalker
    stalker = Stalker()

    if ARGS.save_new:
        names = conf['CHANNEL_SAVE_ALL']
        asyncio.run(stalker.scan(names=names))
    if ARGS.stalk_regex:
        names = conf['CHANNEL_STALK_REGEX'].keys()
        asyncio.run(stalker.scan(names=names, only_regex=True))
        print_to_discord("Tg_stalker stalk_regex checked")


if __name__ == '__main__':
    print_to_discord("Tg_stalker started")
    main()



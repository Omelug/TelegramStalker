try:
    import traceback
    import re
    import traceback
    import os
    from tg_log import *
    from tg_db import *
    from discord_webhook import DiscordWebhook
    from input_parser import InputParser
    from lockfile import FileLock, LockTimeout
    from telethon import TelegramClient
    from telethon.errors import MsgIdInvalidError, PeerIdInvalidError, ChannelInvalidError, InputUserDeactivatedError, \
    ChannelPrivateError
    from telethon.tl.functions.messages import GetHistoryRequest, GetRepliesRequest
except KeyboardInterrupt:
    print("\nKeyboardInterrupt during import of modules", file=sys.stderr)
    sys.exit(1)



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
    if regex_list is None:
        return True
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

async def get_messages(client, offset_id: int, channel_name):
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
        return None
    return history.messages


async def get_all_replies(channel_name, message, client):
    offset_id = 0
    all_replies = []

    try:
        # Convert the channel name to InputPeerChannel
        peer = await client.get_input_entity(channel_name)
    except PeerIdInvalidError:
        print(f"Invalid channel name: {channel_name}")
        return []
    except (ChannelInvalidError, ChannelPrivateError, InputUserDeactivatedError) as e:
        print(f"Error retrieving entity for channel {channel_name}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

    while True:
        try:
            #print(f"Requesting replies for {channel_name} with offset_id {offset_id}")
            replies = await client(GetRepliesRequest(
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
            print(f"Invalid peer used in GetRepliesRequest for channel: {channel_name}")
            break
        except Exception as e:
            print(f"Unexpected error while fetching replies: {e}")
            break
    return all_replies


async def save_replies(session,client,channel_name, message=None, regex_list=[], msg_saved=False, inserted_id=None, stats=None):
    if not conf['ignore_replies']:
        try:

            replies = await get_all_replies(channel_name, message, client)
            print_d(f"Loaded {len(replies)} replies for {message.id}")

            # Prepare a list to store all replies
            replies_for_save = []
            author_ids = {}

            for reply in replies:
                match = regex_check(regex_list, reply.message, echo=True)
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

            # Insert all replies in one batch
            if replies_for_save:
                await insert_replies(session, replies_for_save)
        except MsgIdInvalidError: # no replies
            pass
        except Exception as e:
            print(f"comments Error  {type(e).__name__}")
            traceback.print_exc()

    await session.commit()


async def tg_download(message, regex_list):
    if (conf['download_regex_files'] and message.file and
            regex_check(regex_list, message.file.name, echo=True)):
        await message.download_media(file="./downloads/")
        return True
    return False


async def save_all_after(session, client, channel_name, last_seen, max_history=conf['max_requests'], offset_id=0, regex_list=None):

    stats = {"replies_c": 0,'message_c':0, "msg_insert": 0}
    try:
        for req_count, _ in enumerate(range(max_history)):
            print(f"{req_count=}/{max_history}")

            #save messages
            messages = await get_messages(client,offset_id, channel_name)
            if messages is None:
                return
            stats['message_c'] += len(messages)
            print_d(f"Loaded {len(messages)} messages")

            for message in (message for message in messages if message.message is not None):
                if last_seen is not None and message.date.replace(tzinfo=None) <= last_seen:
                    return

                # Download files
                downloaded = await tg_download(message, regex_list)

                # Save message if math
                inserted_id = -1
                msg_saved = False
                if regex_check(regex_list, message.message, echo=True) or downloaded:
                    inserted_id = await insert_message(session, message, client, channel_name)
                    msg_saved = True
                    stats['message_insert'] += 1

                #save replies
                await save_replies(session, client, channel_name, message, regex_list, msg_saved=msg_saved, inserted_id=inserted_id, stats=stats)

            offset_id = messages[-1].id
            print(f"{offset_id}\t{stats['msg_insert']}/{stats['message_c']} inserted, {stats['replies_c']} replies")
        return True
    except KeyboardInterrupt:
        session.rollback()
        await update_offset(channel_name, offset_id)
        return False

async def save_channel(client, channel_name: str, only_regex=False):
    async with get_session() as session:
        channel: Channel = await get_channel(session, channel_name)
        compiled_regex_list = None
        if only_regex:
            regex_list = await get_regexes(session, conf['CHANNEL_STALK_REGEX'][channel_name])
            compiled_regex_list = [re.compile(regex) for regex in regex_list]

        offset_id = 0
        if conf['reset'] and channel.offset_id is not None:
            offset_id=channel.offset_id

        if await save_all_after(session, client, channel.name, channel.last_seen, regex_list=compiled_regex_list, offset_id=offset_id):
            channel.last_seen = datetime.now()
            channel.offset_id = None

        await session.commit()

class Stalker():
    def __init__(self):
        self.client = None
        self.queue = asyncio.Queue()

    async def start_client(self):
        self.client = TelegramClient('userbot', conf['API_ID'], conf['API_HASH'])
        await self.client.start(phone=conf['PHONE_NUMBER'])

    async def worker(self, only_regex=False):
        running = True
        while running:
            try:
                channel_name = await self.queue.get()
                print_ok(f"Processing {channel_name}")
                await save_channel(self.client, channel_name, only_regex=only_regex)
                self.queue.task_done()
            except KeyboardInterrupt:
                running = False
                print_e("Waiting for tasks to finish")
            except Exception as e:
                print_e(f"Error processing task {e}")
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
    try:
        ARGS = get_args()
        # print(ARGS.save_new,type(ARGS.save_new))
        global stalker
        stalker = Stalker()

        if ARGS.save_new:
            names = conf['CHANNEL_SAVE_ALL']
            asyncio.run(stalker.scan(names=names))
        if ARGS.stalk_regex:
            if conf['download_regex_files']:
                os.makedirs('./downloads', exist_ok=True)
            names = conf['CHANNEL_STALK_REGEX'].keys()
            asyncio.run(stalker.scan(names=names, only_regex=True))
            print_to_discord("Tg_stalker stalk_regex checked")
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    print_to_discord("Tg_stalker started")
    main()



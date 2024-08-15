import re
import json
import html
import sys

async def save_messages(messages):

    for message in messages:
        msg = re.sub(r'<.*?>', r' ', message.message)
        msg = re.sub(r'\\', r' ', msg)
        match = re.search(r"({.*})", msg, re.DOTALL)

        if not match:
            print("No JSON object found in the text.", file=sys.stderr)
            print(message.message, file=sys.stderr)
            continue
        try:
            in_json = json.loads(match.group(1))

            msg_json = {
                "channel_name": CHANNEL_NAME,
                "date": str(message.date),
                "msg_id": message.id,
                "source": in_json["Source"],
                "content": in_json["Content"],
                "author": html.unescape(in_json["author"]),
                "detection_date": in_json["Detection Date"],
                "type": in_json["Type"]
            }
        except json.decoder.JSONDecodeError as e:
            print(message.message)
            print(e.msg)

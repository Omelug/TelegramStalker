
   /$$               /$$
  | $$              | $$
 /$$$$$$    /$$$$$$ | $$  /$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$  /$$$$$$/$$$$
|_  $$_/   /$$__  $$| $$ /$$__  $$ /$$__  $$ /$$__  $$|____  $$| $$_  $$_  $$
  | $$    | $$$$$$$$| $$| $$$$$$$$| $$  \ $$| $$  \__/ /$$$$$$$| $$ \ $$ \ $$
  | $$ /$$| $$_____/| $$| $$_____/| $$  | $$| $$      /$$__  $$| $$ | $$ | $$
  |  $$$$/|  $$$$$$$| $$|  $$$$$$$|  $$$$$$$| $$     |  $$$$$$$| $$ | $$ | $$
   \___/   \_______/|__/ \_______/ \____  $$|__/      \_______/|__/ |__/ |__/
                               /$$ /$$  \ $$     /$$ /$$
                              | $$|  $$$$$$/    | $$| $$
                    /$$$$$$$ /$$$$$$____/$$$$$$ | $$| $$   /$$  /$$$$$$   /$$$$$$
                   /$$_____/|_  $$_/   |____  $$| $$| $$  /$$/ /$$__  $$ /$$__  $$
                  |  $$$$$$   | $$      /$$$$$$$| $$| $$$$$$/ | $$$$$$$$| $$  \__/
                   \____  $$  | $$ /$$ /$$__  $$| $$| $$_  $$ | $$_____/| $$
                   /$$$$$$$/  |  $$$$/|  $$$$$$$| $$| $$ \  $$|  $$$$$$$| $$
                  |_______/    \___/   \_______/|__/|__/  \__/ \_______/|__/

For advice, feedback, or help, contact me:

Discord: gulemo
Github: https://github.com/Omelug

__________________________________________________________________
INSTALLATION:
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
On Linux:
    sudo apt-get install python3 python3-pip
    make venv_init && source .venv/bin/activate (if you want venv)
    make install

1/make venv_init && .venv/bin/activate
2/make install

__________________________________________________________________
BEFORE START:
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

requirements: python3, postgresSQL link

1/ create postgresSQL database
2/ Run "python3 tg_config.py --generate_default" for generating config.json
3/ edit database connection in ftp_secret.py (optionally edit config.json)
4/ tg_secret.py is main script, good luck

__________________________________________________________________
USAGE:
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

In config.json you can set the channels to be monitored
(You can rewrite it directly in tg_stalker.py, but config.json rewrite it, you can delete config.py and it will work)

CHANNEL_SAVE_ALL are the channels that will be saved
CHANNEL_STALK_REGEX is dict in format {<name>:{<regex_name>, <second_regex_name>}}
You can add regexes to default_regexes or add it to database after first start
Change WEBHOOK / DEFAULT users ids (if you want to be notified on discord)

for first time you need to 2FA login code

Dont forget "source .venv/bin/activate" if you are using venv

__________________________________________________________________
tg_stalker.py
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
usage: tg_stalker.py [-h] [--save_new] [--stalk_regex]

options:
  -h, --help     show this help message and exit
  --save_new     Save new messages from channels in CHANNEL_SAVE_ALL
  --stalk_regex  Stalk with regex channel in CHANNEL_STALK_REGEX

__________________________________________________________________
TODO
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

1/ async downloading from telegram - It uses only one users now,
    idk if is the big problem, it is not priority now
2/ download of regex dont works (and it is not priority yes)
3/ WTF some weird errors during replies downloading
4/ checking already running scripts is heavy (I think it is cause by tg_db.py init)


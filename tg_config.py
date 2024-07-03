import json
import os
import sys

secret_file = "tg_secret.py"
if not os.path.exists(secret_file):
    with open(secret_file, 'w+') as f:
        print("DATABASE_URL_ASYNC = 'postgresql+asyncpg://<database username>:<password>@localhost:5432/<db_name>'", file=f)
        print("PHONE_NUMBER = '+420720417270'", file=f)
        print("API_HASH = '7e65ea367a7c27bf9559828fa38026a5'", file=f)
        print("API_ID = 123456", file=f)
        print(f"Please, edit {secret_file}")
    exit(0)
else:
    import tg_secret

DEFAULT_CONFIG = {
    'all':{
        'DEBUG': True
    },
    'tg_stalker': {
        'OUTPUT': "message_log.json",
        'CHANNEL_SAVE_ALL': ['svoboda365diskuze'],
        'CHANNEL_SAVE_ALL______': ['stacilocz', 'covidlogika','selskyrozum',
                             'zakonybohatstvi','neCT24', 'otevrisvoumysl',
                             'cz24news','absurdnisvet','lubomirvolnyoficialni',
                             'svoboda365','ceskadomobrana','svoboda365diskuze',
                             'lubomirvolnyoficialni', 'otevrisvoumysl', 'zakonybohatstvi',
                                   'nsfronta'],
        'CHANNEL_STALK_REGEX': {'breachdetector': {'CZ_REGEX', 'SK_REGEX'},
                                'nohidespace': {'CZ_REGEX', 'SK_REGEX'},
                                'mailpass_chat': {'CZ_REGEX', 'SK_REGEX'},
                                'mail_mailaccess' : {'CZ_REGEX', 'SK_REGEX'},
                                'SunriseDataFree' : {'CZ_REGEX', 'SK_REGEX'},
                                'Redhash': {'CZ_REGEX', 'SK_REGEX'},
                                'leaked_detabase' : {'CZ_REGEX', 'SK_REGEX'},
                                'crackcodes' : {'CZ_REGEX', 'SK_REGEX'},
                                'baseleak' : {'CZ_REGEX', 'SK_REGEX'},
                                'dbforall' : {'CZ_REGEX', 'SK_REGEX'},
                                },
        'OPTION_FILE': "options.json",
        'DISCORD': False,
        'DEFAULT_USERS': ["503629068319588407"],
        'WEBHOOK': "https://discord.com/api/webhooks/1247872452617572486/xkbg2luX_48wKHElCLXpAjypx5Mvq1t_O57kfJknr6tWXrOnmdxU9h7P02BazwGnKRJ1",
        'API_ID': tg_secret.API_ID,
        'API_HASH': tg_secret.API_HASH,
        'PHONE_NUMBER': tg_secret.PHONE_NUMBER,
        'max_workers': 1,
        'max_requests': 100000,
        'color_output': True,
        'regex_all_comments': False,
        'ignore_replies': False,
        'reset': True,
        'download_regex_files': False
    },
    'tg_db': {
        'DATABASE_URL_ASYNC': tg_secret.DATABASE_URL_ASYNC,
    },
    'default_regexes': {
        "CZ_REGEX" : r'czech|databáze|česk|prague|praha|[^a-zA-Z]cz[^a-zA-Z]',
        "SK_REGEX" : r'slovak|databáza|bratislav|[^a-zA-Z]sk[^a-zA-Z]',
        "EU_REGEX" : r'Europe|[^a-zA-Z]eu[^a-zA-Z]'
    }
}
global CONFIG

def generate_default():
    with open("config.json", 'w') as f:
        json.dump(CONFIG, f, indent=4)

def load_config(config_file="config.json"):
    global CONFIG
    CONFIG = DEFAULT_CONFIG.copy()
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = json.load(f)
        CONFIG.update(file_config)
load_config()

if __name__ == "__main__":
    if '--generate_default' in sys.argv:
        generate_default()
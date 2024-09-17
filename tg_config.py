import configparser
import json
import os
import sys

secret_file = "tg_secret.ini"
if not os.path.exists(secret_file):
    config = configparser.ConfigParser()
    config['postgres_stalk'] = {
        'user': '<database username>',
        'password': '<password>',
        'name': '<db_name>',
        'host': 'localhost',
        'port': '5432'
    }
    config['postgres_stalk'] = {
        'user': '<database username>',
        'password': '<password>',
        'name': '<db_name>',
        'host': 'localhost',
        'port': '5432'
    }
    config['telegram'] = {
        'PHONE_NUMBER': '<phone number>',
        'API_HASH': '<API HASH>',
        'API_ID': '<API ID>'
    }
    config['discord'] = {
        'WEBHOOK': 'https://discord.com/api/webhooks/....',
        'DEFAULT_USERS': 'user_id,second_user_id'
    }

    with open(secret_file, 'w') as configfile:
        config.write(configfile)
    print(f"Please, edit {secret_file}")
    exit(0)

else:
    config = configparser.ConfigParser()
    config.read(secret_file)

    DB_USER_STALK = config['postgres_stalk']['user']
    DB_PASSWORD_STALK = config['postgres_stalk']['password']
    DB_HOST_STALK = config['postgres_stalk']['host']
    DB_PORT_STALK = config['postgres_stalk']['port']
    DB_NAME_STALK = config['postgres_stalk']['name']

    DATABASE_URL_STALK_REGEX = f"postgresql+asyncpg://{DB_USER_STALK}:{DB_PASSWORD_STALK}@{DB_HOST_STALK}:{DB_PORT_STALK}/{DB_NAME_STALK}"

    DB_USER_SAVE = config['postgres_save']['user']
    DB_PASSWORD_SAVE = config['postgres_save']['password']
    DB_HOST_SAVE = config['postgres_save']['host']
    DB_PORT_SAVE = config['postgres_save']['port']
    DB_NAME_SAVE = config['postgres_save']['name']

    DATABASE_URL_SAVE_NEW = f"postgresql+asyncpg://{DB_USER_SAVE}:{DB_PASSWORD_SAVE}@{DB_HOST_SAVE}:{DB_PORT_SAVE}/{DB_NAME_SAVE}"

    PHONE_NUMBER = config['telegram']['PHONE_NUMBER']
    API_HASH = config['telegram']['API_HASH']
    API_ID = config['telegram']['API_ID']

    WEBHOOK = config['discord']['WEBHOOK']
    DEFAULT_USERS = config['discord']['DEFAULT_USERS'].split(',')

DEFAULT_CONFIG = {
    'all':{
        'DEBUG': True,
        'timezone': 'Etc/GMT-2'
    },
    'tg_stalker': {
        'OUTPUT': "message_log.json",
        'CHANNEL_SAVE_ALL': ['stacilocz','covidlogika','selskyrozum',
                             'zakonybohatstvi','neCT24', 'otevrisvoumysl',
                             'cz24news',
                             'svoboda365','ceskadomobrana',
                             'lubomirvolnyoficialni', 'otevrisvoumysl', 'zakonybohatstvi',
                             'nsfronta'],
        'CHANNEL_STALK_REGEX': {'breachdetector': {'CZ_REGEX', 'SK_REGEX'},
                                'nohidespac': {'CZ_REGEX', 'SK_REGEX'},
                                'RansomFeedNews': {'CZ_REGEX', 'SK_REGEX'},
                                'sellbuydatabasecommunity': {'CZ_REGEX', 'SK_REGEX'},
                                'SunriseDataFree' : {'CZ_REGEX', 'SK_REGEX'},
                                'Redhash': {'CZ_REGEX', 'SK_REGEX'},
                                'leaked_detabase' : {'CZ_REGEX', 'SK_REGEX'},
                                'crackcodes' : {'CZ_REGEX', 'SK_REGEX'},
                                'baseleak' : {'CZ_REGEX', 'SK_REGEX'},
                                'CyberArmyofRussia_Reborn': {'CZ_REGEX', 'SK_REGEX'},
                                'noname05716': {'CZ_REGEX', 'SK_REGEX'},
                                'mailaccessmegacloud': {'CZ_REGEX', 'SK_REGEX'},
                                'MAilAccessCracker': {'CZ_REGEX', 'SK_REGEX'},
                                'COMBO_MAILACCESS': {'CZ_REGEX', 'SK_REGEX'},
                                'Mailaccess_live_data_kaidnomorr': {'CZ_REGEX', 'SK_REGEX'},
                                'mailaccessbeast': {'CZ_REGEX', 'SK_REGEX'},
                                'AntiPlumbers': {'CZ_REGEX', 'SK_REGEX'},
                                'cRyPtHoN_INFOSEC_EN':{'CZ_REGEX', 'SK_REGEX'},
                                'ransomwatcher':{'CZ_REGEX', 'SK_REGEX'},
                                'canyoupwnme':{'CZ_REGEX', 'SK_REGEX'},
                                'changesetting':{'CZ_REGEX', 'SK_REGEX'},
                                },
        'OPTION_FILE': "options.json",
        'DISCORD': True,
        'WEBHOOK': WEBHOOK,
        'DEFAULT_USERS': DEFAULT_USERS,
        'API_ID': API_ID,
        'API_HASH': API_HASH,
        'PHONE_NUMBER': PHONE_NUMBER,
        'max_workers': 1,
        'max_requests': 100000,
        'color_output': True,
        'regex_all_comments': True,
        'ignore_replies': False,
        'reset': True,
        'download_regex_files': False
    },
    'tg_db': {
        'DATABASE_URL_ASYNC':None,
        'DATABASE_URL_STALK_REGEX': DATABASE_URL_STALK_REGEX,
        'DATABASE_URL_SAVE_NEW': DATABASE_URL_SAVE_NEW,
    },
    'default_regexes': {
        "CZ_REGEX" : r'czech|databáze|česk|prague|praha|[^a-zA-Z]cz[^a-zA-Z]',
        "SK_REGEX" : r'slovak|databáza|bratislav|[^a-zA-Z]sk[^a-zA-Z]',
        "EU_REGEX" : r'Europe|[^a-zA-Z]eu[^a-zA-Z]'
    }
}
global CONFIG

def generate_default():
    def default_encoder(obj):
        try:
            return json.JSONEncoder().default(obj)
        except TypeError:
            return str(obj)  # Convert non-serializable objects to strings

    with open("config.json", 'w') as f:
        json.dump(CONFIG, f, indent=4, default=default_encoder)

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
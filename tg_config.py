import tg_secret

CONFIG = {
    'tg_stalker': {
        'OUTPUT': "message_log.json",
        'CHANNEL_SAVE_ALL': ['stacilocz', 'covidlogika','selskyrozum','zakonybohatstvi','neCT24', 'otevrisvoumysl','cz24news','absurdnisvet','lubomirvolnyoficialni','svoboda365','ceskadomobrana'],
        'CHANNEL_STALK_REGEX': {'breachdetector':
                                    {'CZ_REGEX', 'SK_REGEX'}
                                },
        'OPTION_FILE': "options.json",
        'DISCORD': True,
        'DEFAULT_USERS': ["503629068319588407"],
        'WEBHOOK': "https://discord.com/api/webhooks/1247872452617572486/xkbg2luX_48wKHElCLXpAjypx5Mvq1t_O57kfJknr6tWXrOnmdxU9h7P02BazwGnKRJ1",
        'API_ID': tg_secret.API_ID,
        'API_HASH': tg_secret.API_HASH,
        'PHONE_NUMBER': tg_secret.PHONE_NUMBER,
        'max_workers': 15,
        'max_requests': 100000,
        'color_output': True,
        'regex_all_comments': True,
        'ignore_replies': True,
        'offset_id': 0
    },
    'tg_db': {
        'DATABASE_URL_ASYNC': tg_secret.DATABASE_URL_ASYNC,
    },
    'default_regexes': {
        "CZ_REGEX" : r'czech|databáze|česk|prague|praha|[\.\- _,]cz[\.\- _,]',
        "SK_REGEX" : r'slovak|databáza|bratislav|[\.\- _,]sk[\.\- _,]'
    }
}
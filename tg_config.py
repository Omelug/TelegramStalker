import tg_secret

CONFIG = {
    'tg_stalker': {
        'OUTPUT': "message_log.json",
        'CHANNEL_SAVE_ALL': ['svoboda365diskuze'],
        'CHANNEL_SAVE_ALL______': ['stacilocz', 'covidlogika','selskyrozum',
                             'zakonybohatstvi','neCT24', 'otevrisvoumysl',
                             'cz24news','absurdnisvet','lubomirvolnyoficialni',
                             'svoboda365','ceskadomobrana','svoboda365diskuze'],
        'CHANNEL_STALK_REGEX': {'breachdetector': {'CZ_REGEX', 'SK_REGEX'},
                                'nohidespace': {'CZ_REGEX', 'SK_REGEX', 'EU_REGEX'}
                                },
        'OPTION_FILE': "options.json",
        'DISCORD': True,
        'DEFAULT_USERS': ["503629068319588407"],
        'WEBHOOK': "https://discord.com/api/webhooks/1247872452617572486/xkbg2luX_48wKHElCLXpAjypx5Mvq1t_O57kfJknr6tWXrOnmdxU9h7P02BazwGnKRJ1",
        'API_ID': tg_secret.API_ID,
        'API_HASH': tg_secret.API_HASH,
        'PHONE_NUMBER': tg_secret.PHONE_NUMBER,
        'max_workers': 2,
        'max_requests': 100000,
        'color_output': True,
        'regex_all_comments': True,
        'ignore_replies': False,
        'offset_id': 0,
        'download_regex_files': True
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
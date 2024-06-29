How to start:

What is not done yet:
 - input parser
 - async downloading from telegram - It uses only one users now,
    idk if is the big problem, it is not priority now

A / create file secret.py with the following content:
    1. - create database tg_stalker in postgres (tested on postgresql 16)
    DATABASE_URL_ASYNC = "postgresql+asyncpg://<db_username>:<db_password>@<server_ip>/tg_stalker"

    2. - create telegram app and get api_id and api_hash
    API_ID =
    API_HASH =
    PHONE_NUMBER = '<phone_number for telegram login>'

    3. in tg_config
        - add/change the list for the channels to be monitored
        - change discord web hook if you want to be notified on discord / DEFUALT users ids
        -
B / run the following commands:
    1. pip install -r requirements.txt # todo s input_parserem
    2. python3 tg_stalker.py --help
    3. follow the instructions in the console


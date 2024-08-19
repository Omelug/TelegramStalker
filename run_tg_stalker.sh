# Activate the virtual environment
. /root/TelegramStalker/.venv/bin/activate

# Run the Python script
touch /root/TelegramStalker/stalk_regex.log
touch /root/TelegramStalker/save_new.log

python3 /root/TelegramStalker/tg_stalker.py --stalk_regex 2>&1 | tee -a /root/TelegramStalker/stalk_regex.log
python3 /root/TelegramStalker/tg_stalker.py --save_new  2>&1 | tee -a /root/TelegramStalker/save_new.log


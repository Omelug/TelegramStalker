USERNAME = root
# change if you use different server xd
SERVER = 45.134.226.157
DEST_DIR = /root/TelegramStalker
CODE_FILEs = ./*.py ./Makefile ./run_tg_stalker.sh tg_secret.ini requirements.txt
.PHONY: code_to_server

code_to_server: FORCE
	rsync -avz  $(CODE_FILEs) $(USERNAME)@$(SERVER):$(DEST_DIR)

venv_init:
	python3 -m venv .venv

req_save:
	pip3 freeze > requirements.txt

install: FORCE
	pip3 install git+https://github.com/Omelug/python_mini_modules.git#egg=input_parser
	pip3 install -r requirements.txt

FORCE:
from colorama import Fore, Style
import sys
from tg_config import CONFIG

def print_e(string, condition=True):
    if condition:
        if CONFIG['tg_stalker']['color_output']:
            print(f"{Fore.RED}{string}{Fore.RESET}", file=sys.stderr)
        else:
            print(string, file=sys.stderr)


def print_d(msg):
    if CONFIG['all']['DEBUG']:
        print(Fore.GREEN + msg + Fore.RESET, file=sys.stderr)


def print_ok(msg, **kwargs):
    if CONFIG['tg_stalker']['color_output']:
        print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET, kwargs)
    else:
        print(msg, kwargs)

def print_s(msg):
    print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET, file=sys.stderr)

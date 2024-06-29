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
    print(Fore.GREEN + msg + Fore.RESET, file=sys.stderr)


def print_ok(msg):
    if CONFIG['tg_stalker']['color_output']:
        print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET)
    else:
        print(msg)

def print_s(msg):
    print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET, file=sys.stderr)

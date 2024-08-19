from colorama import Fore, Style
import sys
from tg_config import CONFIG

def print_e(string, condition=True, **kwargs):
    if condition:
        if CONFIG['tg_stalker']['color_output']:
            print(f"{Fore.RED}{string}{Fore.RESET}", flush=True, file=sys.stderr,**kwargs)
        else:
            print(string, file=sys.stderr,**kwargs)

def print_d(msg,**kwargs):
    if CONFIG['all']['DEBUG']:
        print(Fore.GREEN + msg + Fore.RESET, file=sys.stderr, flush=True,**kwargs)

def print_ok(msg, **kwargs):
    if CONFIG['tg_stalker']['color_output']:
        print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET,flush=True, **kwargs)
    else:
        print(msg, **kwargs, flush=True)

def print_s(msg):
    print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET, flush=True,file=sys.stderr)

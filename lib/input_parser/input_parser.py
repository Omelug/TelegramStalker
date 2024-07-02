#!/usr/bin/env python3
import argparse
import sys


def arg_input(action, in_msg):
    while True:
        try:
            user_input = input(in_msg)
            if action.type == bool:
                if str(user_input).lower() in ["true", "f", "yes", "y"]:
                    user_input = True
                elif str(user_input).lower() in ["false", "f", "no", "n"]:
                    user_input = False
                else:
                    raise ValueError()
            else:
                user_input = action.type(user_input)
            return user_input
        except ValueError:
            print(f"Invalid input for {action.dest}. Expected type: {action.type}")

class InputParser(argparse.ArgumentParser):
    input_args = {}

    def add_argument(self, *names, **kwargs):
        #print(kwargs)
        input_prompt = kwargs.pop('input', None)
        need=kwargs.pop('required', False)
        #print(need)
        super().add_argument(*names, **kwargs)
        if need:
            key = names[-1].lstrip('-')
            self.input_args[key] = {"input": input_prompt}

        return self

    def parse_args(self, args=None, namespace=None):
        args = super().parse_args(args, namespace)
        try:
            for action in self._actions:
                #print(f"{self.input_args}")
                if action.dest != "help" and getattr(args, action.dest) is None and action.dest in self.input_args.keys():
                    in_msg = self.input_args.get(action.dest).get("input")
                    print(f"--{action.dest}\t ", end="", file=sys.stderr)
                    if in_msg is None:
                        in_msg = f"Need value for {action.dest}: "
                    user_input = arg_input(action, in_msg)
                    setattr(args, action.dest, user_input)
        except KeyboardInterrupt:
            sys.exit(1)
        return args

    def str_command(self, args):
        full_cmd = [f"{sys.argv[0]}"]
        for action in self._actions:
            if action.dest != "help":
                full_cmd.append(f"--{action.dest} {getattr(args, action.dest)}")
        return " ".join(full_cmd)

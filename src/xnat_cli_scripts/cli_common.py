#!/bin/python3


import argparse
from typing import Union
import json
import sys

# Common functions for CLI executables

def extract_auth_user(args: argparse.Namespace) -> str:
    if (args.auth is None):
        return "NoUser"

    return args.auth.split(":")[0]

def extract_auth_password(args: argparse.Namespace) -> Union[str,None]:
    if (args.auth is None):
        return None

    auth_tokens = args.auth.split(":")
    auth_password=None

    if len(auth_tokens) > 1:
        auth_password = auth_tokens[1]
    elif args.password is not None:
        auth_password = args.password

    return auth_password

def extract_extension_types(args: argparse.Namespace) -> bool:
    if (args.extension_types is not None and args.extension_types == "True"):
        return True

    return False

def read_text_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        content = file.read()
        file.close()
        return content

def read_json_file(file_path: str):
    with open(file_path, "r") as file:
        content = json.load(file)
        file.close()
        return content

def apply_sleep(args: argparse.Namespace) -> None:
    """ Applies sleep if -s is specified """
    if args.sleep:
        try:
            sleep_time = float(args.sleep)
            if sleep_time > 0:
                time.sleep(sleep_time)
        except ValueError:
            print("[ERROR] Invalid sleep value. Please provide a valid number.")

def print_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def convert_array_to_string(input_array, delimiter:str) -> str:
    rtn = ""
    for index in range(len(input_array) - 1) :
        rtn += input_array[index] + "\t"

    rtn += input_array[len(input_array)-1]

    return rtn
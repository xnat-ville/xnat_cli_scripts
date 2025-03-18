#!/bin/python3
"""
investigators.py
---
Handles investigator JSON extraction from XNAT.

Example usage:
    Get investigator JSON files:
        python3 -m xnat_cli_scripts.investigators --get --investigator_json --output_folder investigator_json
"""

import argparse
import requests
import xnat
import xnat.core
import xnat.mixin
from xnat.session import XNATSession
import time
import warnings
from pathlib import Path
import json 
import xnat_cli_scripts.cli_common

warnings.filterwarnings('ignore')

def apply_sleep(args: argparse.Namespace) -> None:
    """Applies sleep if -s is specified"""
    if args.sleep:
        try:
            sleep_time = float(args.sleep)
            if sleep_time > 0:
                time.sleep(sleep_time)
        except ValueError:
            print("[ERROR] Invalid sleep value. Please provide a valid number.")

def execute_get_investigator_json(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    
    #Retrieves investigator data from XNAT and saves each investigator as an individual JSON file.
    
    output_folder = args.output_folder if args.output_folder else "test_data/investigator_json"
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Fetch investigator data from the API
    response = connection.get_json("/xapi/investigators")
    apply_sleep(args)

    for investigator in response:
        investigator_id = investigator.get('xnatInvestigatordataId')  

        if not investigator_id:  # Skip if no ID found
            print(f"[WARNING] Investigator missing ID, skipping.")
            continue

        # Save JSON with only the ID as filename
        file_name = f"{output_folder}/{investigator_id}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(investigator, f, indent=4)

    print(f"Successfully saved investigator JSON files")



def execute_get_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if args.get and args.investigator_json:
        execute_get_investigator_json(connection, args)
    else:
        print("[WARNING] No valid GET action specified. Use --get --investigator_json.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract investigator JSON from XNAT")
    parser.add_argument('-x', '--xnat', dest='url', help="URL to XNAT instance", required=True)
    parser.add_argument('-a', '--auth', dest='auth', help="User authentication/login", required=True)
    parser.add_argument('-p', '--password', dest='password', help="Password for XNAT authentication", required=False)
    parser.add_argument('-e', '--extension_types', dest='extension_types', help="True or False for extension_types in xnat.connect")

    parser.add_argument('--get', dest='get', help="Action to GET investigator JSON", action='store_true')
    parser.add_argument('--investigator_json', dest='investigator_json', help="Extract investigator JSON", action='store_true')
    parser.add_argument('--output_folder', dest='output_folder', help="Folder to store investigator JSON files")
    parser.add_argument('-s', '--sleep', dest='sleep', help="Time to sleep after each REST call")

    args = parser.parse_args()

    auth_user = xnat_cli_scripts.cli_common.extract_auth_user(args)
    auth_password = xnat_cli_scripts.cli_common.extract_auth_password(args)
    xnat_extensions = xnat_cli_scripts.cli_common.extract_extension_types(args)

    session = xnat.connect(args.url, user=auth_user, password=auth_password, extension_types=xnat_extensions)

    if args.get:
        execute_get_master(session, args)
    else:
        print("[ERROR] No valid action specified. Use --get.")

    session.disconnect()

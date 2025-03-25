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
import time
import warnings
from pathlib import Path
from os import listdir
import json
import csv
import requests
import xnat
import xnat.core
import xnat.mixin
from xnat.session import XNATSession

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

def execute_list_investigators(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    """
    Handles listing of investigators from the XNAT system.

    If --csv is provided, limits the output to investigator IDs listed in the CSV file.
    Outputs a tab-delimited list with the following fields:
    xnatInvestigatordataId, lastname, firstname, email, institution
    """

    # Optional filtering
    filter_ids = set()
    if args.csv:
        try:
            with open(args.csv, newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    for cell in row:
                        cell = cell.strip()
                        if cell.isdigit():
                            filter_ids.add(int(cell))
        except Exception as e:
            print(f"[ERROR] Could not read CSV filter file: {e}")
            return

    try:
        response = connection.get_json("/xapi/investigators")
    except Exception as e:
        print(f"[ERROR] Failed to fetch investigators: {e}")
        return

    apply_sleep(args)

    for inv in response:
        inv_id = inv.get("xnatInvestigatordataId")
        if not inv_id:
            continue
        if filter_ids and inv_id not in filter_ids:
            continue

        print(f"{inv_id}\t{inv.get('lastname','')}\t{inv.get('firstname','')}\t{inv.get('email','')}\t{inv.get('institution','')}")

def execute_list_investigator_pis(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Lists investigators who are primary PIs for projects.
    Output: investigator_id<TAB>project_id (one line per project).
    Optional CSV filter limits by investigator ID.
    """

    # Load investigator ID filter (if any)
    filter_ids = set()
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as f:
                reader = csv.reader(f, delimiter='\t')
                for row in reader:
                    for cell in row:
                        cell = cell.strip()
                        if cell.isdigit():
                            filter_ids.add(int(cell))
        except Exception as e:
            print(f"[ERROR] Failed to read CSV filter: {e}")
            return

    try:
        response = connection.get_json("/xapi/investigators")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve investigator data: {e}")
        return

    apply_sleep(args)

    for inv in response:
        inv_id = inv.get("xnatInvestigatordataId")
        if not inv_id:
            continue
        if filter_ids and inv_id not in filter_ids:
            continue

        primary_projects = inv.get("primaryProjects", [])
        for project_id in primary_projects:
            print(f"{inv_id}\t{project_id}")

def execute_list_master(connection:xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if args.pi:
        execute_list_investigator_pis(connection,args)
    else:
        execute_list_investigators(connection,args)   

def execute_get_investigator_json(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves investigator data from XNAT and saves each investigator as an individual JSON file.
    Requires --output_folder to be specified.
    """

    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    # Fetch investigator data from the API
    response = connection.get_json("/xapi/investigators")
    apply_sleep(args)

    for investigator in response:
        investigator_id = investigator.get('xnatInvestigatordataId')

        if not investigator_id:
            print("[WARNING] Investigator missing ID, skipping.")
            continue

        # Save each investigator JSON using their ID as the filename
        file_path = f"{args.output_folder}/{investigator_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(investigator, f, indent=4)

    print("[INFO] Successfully saved investigator JSON files.")

def execute_get_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if args.investigator_json:
        execute_get_investigator_json(connection, args)
    else:
        print("[WARNING] No valid GET action specified. Use --get --investigator_json.")


# Reads a folder containing JSON files with individual Investigator records and PUT's them into XNAT
def execute_update_investigator_json(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if args.input_folder is None:
        raise Exception("investigators --update --investigator_json requires --input_folder")

    try:
        http_headers = {}
        http_headers['Content-Type'] = 'application/json'
        listing = listdir(args.input_folder)
        for f in listing:
            print(f)
            with open(f"{args.input_folder}/{f}") as json_file:
                components = f.split('.')
                investigator_id = components[0]
                put_path=f"/xapi/investigators/{investigator_id}"
                connection.put(put_path, data=json_file, headers=http_headers)
                json_file.close()

    except Exception as e:
        raise Exception(f"[ERROR] Exception while reading through folder: {args.input_folder}\n{e}")

    print(f"Successfully updated investigator JSON files")

def execute_update_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if args.investigator_json:
        execute_update_investigator_json(connection, args)
    else:
        print("[WARNING] No valid update action specified. Use --update --investigator_json.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract investigator JSON from XNAT")
    parser.add_argument('-x', '--xnat',              dest='url',                help="URL to XNAT instance",             required=True)
    parser.add_argument('-a', '--auth',              dest='auth',               help="User authentication/login",        required=True)
    parser.add_argument('-p', '--password',          dest='password',           help="Password for XNAT authentication", required=False)
    parser.add_argument('-e', '--extension_types',   dest='extension_types',    help="True or False for extension_types in xnat.connect")

    ## These are operations
    parser.add_argument(      '--list',              dest='list',               help="Action is LIST",                   action='store_true')
    parser.add_argument(      '--get',               dest='get',                help="Action is GET",                    action='store_true')
    parser.add_argument(      '--update',            dest='update',             help='Action is UPDATE (PUT)',           action='store_true')

    # These are objects of the operations
    parser.add_argument(      '--investigator_json', dest='investigator_json',  help="Extract investigator JSON",       action='store_true')
    parser.add_argument(      '--pi',                dest='pi',                 help="Used for PI_ID and project_ID",   action='store_true')
    parser.add_argument(      '--output_folder',     dest='output_folder',      help="Folder to store investigator JSON files")
    parser.add_argument(      '--input_folder',      dest='input_folder',       help="Folder with input JSON files")

    ## Further modifiers
    parser.add_argument(       '--csv',              dest='csv_file',                help='Optional CSV file with investigator IDs to filter')
    parser.add_argument('-s', '--sleep',             dest='sleep',              help="Time to sleep after each REST call")

    args = parser.parse_args()

    auth_user = xnat_cli_scripts.cli_common.extract_auth_user(args)
    auth_password = xnat_cli_scripts.cli_common.extract_auth_password(args)
    xnat_extensions = xnat_cli_scripts.cli_common.extract_extension_types(args)

    session = xnat.connect(args.url, user=auth_user, password=auth_password, extension_types=xnat_extensions)

    if args.list:
        execute_list_master(session, args)
    elif args.get:
        execute_get_master(session, args)
    elif args.update:
        execute_update_master(session, args)
    else:
        print("[ERROR] No valid action specified. Use --get or --update.")

    session.disconnect()

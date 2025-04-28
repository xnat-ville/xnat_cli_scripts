#!/bin/python3
"""
subjects.py
---
--------------------------------------------------------------------------------

This script interacts with a target XNAT instance to list and manage subjects

Example usage:
    List all projects:
        python3 -m xnat_cli_scripts.subjects -L

__version__ = (1, 0, 0)

"""

import argparse
import requests
import csv
import time
import json
from pathlib import Path
import os
from os import listdir
import xnat.mixin
from requests import RequestException
from xnat.session import XNATSession
import xnat_cli_scripts.cli_common


def get_project_ids(connection: XNATSession, args: argparse.Namespace) -> []:
    if args.csv_file:
        project_ids = []
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                if (not row[0].startswith("#")):
                    project_ids.append(row[0])  # Assuming the project ID is in the first column
            file.close()
            return project_ids

    else:
        all_projects = connection.get_json("/data/projects")
        project_ids = [p['ID'] for p in all_projects['ResultSet']['Result']]
        return project_ids

def execute_list_projects_subjects(connection: XNATSession, args: argparse.Namespace) -> None:

    tab="\t"
    project_ids = get_project_ids(connection, args)
    project_count = len(project_ids)
    project_index = 1
    for project_id in project_ids:
        if args.verbose:
            xnat_cli_scripts.cli_common.print_stderr(f"{project_id}{tab}{project_index} / {project_count}")

        get_path = f"/data/projects/{project_id}/subjects"
        subjects_json = connection.get_json(get_path)
        subject_ids = [subject['ID'] for subject in subjects_json['ResultSet']['Result']]
        for subject_id in subject_ids:
            print(f"{project_id}{tab}{subject_id}")
        project_index += 1


def execute_list_master(connection: XNATSession, args: argparse.Namespace) -> None:
    
    if args.projects:
        execute_list_projects_subjects(connection, args)
    else:
        raise Exception("subjects --list requires --projects")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List projects from an XNAT system")
    parser.add_argument('-x', '--xnat',            dest='url',                      help="URL to XNAT, default is https://cnda.wustl.edu")
    parser.add_argument('-a', '--auth',            dest='auth',                     help="User authentication/login for access to XNAT", required=True)
    parser.add_argument('-p', '--password',        dest='password',                 help="Password for XNAT authentication", required=False)
    parser.add_argument('-e', '--extension_types', dest='extension_types',          help="True or False for extension_types in xnat.connect")

    ## These are operations
    parser.add_argument('-L', '--list',            dest='list',                     help="Action is to LIST",                          action='store_true')
    parser.add_argument('-R', '--remove',          dest='remove',                   help='Remove groups from projects',                action='store_true')
    parser.add_argument(        '--update',        dest='update',                   help='Update project accessibilities',             action='store_true')
    parser.add_argument(        '--get',           dest='get',                      help='Get a certain type of object at Project Level', action='store_true')

    # These are objects of the operations;
    parser.add_argument(       '--projects',        dest='projects',                 help='Include project in output',                  action='store_true')
    parser.add_argument(       '--session_json',   dest='session_json',             help="Retrieve session JSONs by session ID",       action='store_true')

    ## Further modifiers
    parser.add_argument('-b', '--brief',           dest='brief_format',             help="List in brief format",                       action='store_true')
    parser.add_argument('-s', '--sleep',           dest='sleep',                    help="Time to sleep after each REST call")
    parser.add_argument('-v', '--verbose',         dest='verbose',                  help="Verbose mode",                               action='store_true')
    parser.add_argument(      '--csv',             dest='csv_file',                 help='Path to CSV file operations such as listing, removing, or changing groups')
    parser.add_argument(      '--input_folder',    dest='input_folder',             help='Path to input folder of files')
    parser.add_argument(      '--output_folder',   dest='output_folder',            help='Path to output folder')
    parser.add_argument(      '--template',        dest='template',                 help='Path to a template file')
    args = parser.parse_args()

    args.url = "localhost:8080" if args.url is None else args.url

    auth_user = xnat_cli_scripts.cli_common.extract_auth_user(args)
    auth_password = xnat_cli_scripts.cli_common.extract_auth_password(args)
    xnat_extensions = xnat_cli_scripts.cli_common.extract_extension_types(args)

    session = xnat.connect(args.url, user=auth_user, password=auth_password, extension_types=xnat_extensions)

try:
    if args.list:
        execute_list_master(session, args)
    else:
        print("[ERROR] No valid action specified. Use -L, -R, --update, or --get.")
finally:
    session.disconnect()  # Ensures cleanup even if an error occurs




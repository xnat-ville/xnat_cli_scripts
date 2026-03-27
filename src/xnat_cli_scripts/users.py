#!/bin/python3
"""
sessions.py
---
--------------------------------------------------------------------------------
This application interacts with a target **XNAT**, and

Example usage of the CLI:
```bash
$ python3  [SCOPE]
```
"""

__version__ = (1, 0, 0)

import argparse
import csv
from time import sleep

import xnat
import xnat.core
import xnat.mixin
import xnat_cli_scripts.cli_common

def execute_list_user_projects(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    target_user = args.target_user
    user_groups = connection.get_json(f"/xapi/users/{target_user}/groups")
    index = 1
    group_length = len(user_groups)
    float_sleep = 0.0
    if (args.sleep is not None):
        float_sleep = float(args.sleep)

    tab = "\t"
    for x_group in user_groups:
        role_index = x_group.rindex("_")
        project_only = x_group[:role_index]
        if args.verbose:
            print(f"{index}{tab}{group_length}{tab}{target_user}{tab}{project_only}")
            index += 1
        else:
            print(f"{target_user}{tab}{project_only}")

        sleep(float_sleep)

def execute_list_user_groups(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    user_array = get_user_array(connection, args)
    user_array.sort()
    tab = "\t"
    output_array = []
    user_index = 0
    row_index = 0

    # First, extract everything into output_array
    for target_user in user_array:
        user_groups = connection.get_json(f"/xapi/users/{target_user}/groups")
        user_groups.sort()
        group_index = 0
        user_index += 1

        for x_group in user_groups:
            row_index += 1
            group_index += 1
            if args.verbose:
                x_string = f"{row_index}{tab}{target_user}{tab}{x_group}"
            else:
                x_string = f"{target_user}{tab}{x_group}"


            output_array.append(x_string)
            print(f"{user_index} {len(user_array)} {group_index} {len(user_groups)}  {x_string}")

    if args.output_csv:
        with open(args.output_csv, "w", encoding="utf-8") as output_csv:
            for x in output_array:
                print(x, file=output_csv)



def execute_list_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if (args.projects):
        execute_list_user_projects(connection, args)
    elif (args.groups):
        execute_list_user_groups(connection, args)
    else:
        print("Request to list requires --groups or --projects")


def remove_user_group(user: str, group: str, sleep_time: float, verbose: bool) -> None:
    print(f"Remove user from group {user} {group} {sleep_time} {verbose}")

def execute_remove_user_groups(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if (args.csv_file is None):
        target_user = args.target_user
        user_groups = connection.get_json(f"/xapi/users/{target_user}/groups")
        for x_group in user_groups:
            remove_user_group(target_user, x_group, args.sleep, args.verbose)

    else:
        with open(args.csv_file, newline='') as csvfile:
            rdr = csv.reader(csvfile, delimiter='\t')
            for row in rdr:
                user = row[0]
                group = row[1]
                remove_user_group(user, group, args.sleep, args.verbose)

def execute_remove_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    if (args.groups):
        execute_remove_user_groups(connection, args)
    else:
        print("Request to remove groups requires --groups")

def execute_user_group_clone(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    source_user = args.clone_groups
    target_user = args.target_user
    user_groups = connection.get_json(f"/xapi/users/{source_user}/groups")
    index = 1
    group_length = len(user_groups)
    float_sleep = 0.0
    if (args.sleep is not None):
        float_sleep = float(args.sleep)

    for x_group in user_groups:
        if args.verbose:
            print(f"{index} {group_length} {source_user} -> {target_user} : {x_group}")
            index += 1

        connection.put(f"/xapi/users/{target_user}/groups/{x_group}")
        sleep(float_sleep)


def get_user_array(connection: xnat.session.XNATSession, args: argparse.Namespace) -> []:
    rtn_array = []
    if (args.target_user):
        rtn_array.append(args.target_user)
        return rtn_array

    rtn_array = connection.get_json(f"/xapi/users")
    return rtn_array



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List projects from an XNAT system")

    ## XNAT user/login information
    parser.add_argument('-x', '--xnat',            dest='url',             help="URL to XNAT, default is https://cnda.wustl.edu")
    parser.add_argument('-a', '--auth',            dest='auth',            help="User authentication/login for access to XNAT", required=True)
    parser.add_argument('-p', '--password',        dest='password',        help="Password for XNAT authentication", required=False)
    parser.add_argument('-e', '--extension_types', dest='extension_types', help="True or False for extension_types in xnat.connect")

    ## These are operations
    parser.add_argument('-L', '--list',            dest='list',            help="Action is to LIST",             action='store_true')
    parser.add_argument('-C', '--clone_groups',    dest='clone_groups',    help='Clone the user group from this user')
    parser.add_argument('-R', '--remove',          dest='remove',          help='Remove role(s) this user',      action='store_true')

    # These are objects of the operations; they regulate the action
    parser.add_argument('-P', '--projects',        dest='projects',        help='Verb object: Projects',         action='store_true')
    parser.add_argument('-g', '--groups',          dest='groups',          help='Verb object: Groups',           action='store_true')
    parser.add_argument('-c', '--csv',             dest='csv_file',        help="CSV file with list of objects (projects, roles, ...) for operations")
    parser.add_argument('--output_csv',            dest='output_csv',      help="Output CSV file")
    parser.add_argument('-t', '--target_user',     dest='target_user',     help='Target user: Operations performed on the target')

    ## Further modifiers
    parser.add_argument('-b', '--brief',           dest='brief_format',    help="List in brief format",          action='store_true')
    parser.add_argument('-s', '--sleep',           dest='sleep',           help="Time to sleep after each REST call")
    parser.add_argument('-v', '--verbose',         dest='verbose',         help="Verbose mode", action='store_true')
    parser.add_argument('-z', '--zebra',           dest='zebra',           help="Zebra mode for testing/debugging", action='store_true')

#    parser.add_argument('-p', '--project',         dest='project_id',      help="Optional Project ID used in list process")
#    parser.add_argument('-d', '--delete',          dest='delete_sessions', help="Action is to DELETE sessions",  action='store_true')
#    parser.add_argument('-r', '--rename',          dest='rename_sessions', help="Action is to RENAME sessions",  action='store_true')

    args = parser.parse_args()

    args.url = "https://cnda.wustl.edu" if args.url is None else args.url
   
    auth_user=xnat_cli_scripts.cli_common.extract_auth_user(args)
    auth_password=xnat_cli_scripts.cli_common.extract_auth_password(args)
    xnat_extensions=xnat_cli_scripts.cli_common.extract_extension_types(args)

    connection = xnat.connect(args.url, user=auth_user, password=auth_password, extension_types=xnat_extensions)

    if args.list:
        execute_list_master(connection, args)
    elif args.remove:
        execute_remove_master(connection, args)
    elif args.clone_groups:
        execute_user_group_clone(connection, args)

    else:
        print("One of the recognized commands was not entered.")

    connection.disconnect()


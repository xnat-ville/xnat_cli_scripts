#!/bin/python3
"""
file_mods.py

"""

import argparse

import warnings
from pathlib import Path
from os import listdir
import json
import xnat_cli_scripts.cli_common

warnings.filterwarnings('ignore')

def remove_from_list(input_list: [], exclusion_list: {}) -> None :
    for x in input_list:
        if x in exclusion_list:
            input_list.remove(x)

def remove_projects_from_investigators(args: argparse.Namespace) -> None:
    if args.output_folder is None:
        print("remove_projects_from_investigators: Missing required argument: output_folder")
        return

    if args.input_folder is None:
        print("remove_projects_from_investigators: Missing required argument: input_folder")
        return

    if args.csv_file is None:
        print("remove_projects_from_investigators: Missing required argument: csv_file")
        return

    inactive_projects = set(open(args.csv_file).read().split())
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)
    try:
        listing = listdir(args.input_folder)
        for f in listing:
            print(f)
            with open(f"{args.input_folder}/{f}") as json_in:
                investigator = json.load(json_in)
                debug_primary=investigator.get("primaryProjects")
                debug_inv_prj=investigator.get("investigatorProjects")
                remove_from_list(investigator.get("primaryProjects"), inactive_projects)
                remove_from_list(investigator.get("investigatorProjects"), inactive_projects)
                json_in.close()
                if ((args.exclude is True) and ((len(investigator.get("primaryProjects")) + len(investigator.get("investigatorProjects"))) == 0)):
                    continue
                file_name = f"{args.output_folder}/{f}"
                with open(file_name, "w", encoding="utf-8") as json_out:
                    json.dump(investigator, json_out, indent=4)


    except Exception as e:
        print(f"[ERROR] Exception while reading through folder: {args.input_folder}")

def determine_index(item_list: [], keyword: str, value: str) -> int :
    index = 0
    while index < len(item_list) :
        item = item_list[index]
        if item[keyword] == value:
            return index
        else:
            index += 1

    return -1

def remove_datatypes_from_projects(args: argparse.Namespace) -> None:
    if args.output_folder is None:
        print("remove_datatypes_from_projects: Missing required argument: output_folder")
        return

    if args.input_folder is None:
        print("remove_datatypes_from_projects: Missing required argument: input_folder")
        return

    if args.csv_file is None:
        print("remove_datatypes_from_projects: Missing required argument: csv_file")
        return

    datatypes_to_remove = set(open(args.csv_file).read().split())
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)
    try:
        listing = listdir(args.input_folder)
        for f in listing:
            with open(f"{args.input_folder}/{f}") as json_in:
                project = json.load(json_in)
                json_in.close()
                items = project['items']
                item_count = len(items)
                item_singular = items[0]
                children = item_singular['children']
                meta = item_singular['meta']
                data_fields = item_singular['data_fields']
                study_protocol_index = determine_index(children, "field", "studyProtocol")
                pre_purge_length = 0
                post_purge_length = 0

                if study_protocol_index > 0:
                    study_protocol_items = children[study_protocol_index]['items']
                    pre_purge_length = len(study_protocol_items)
                    study_protocol_items_post_purge = []
                    for protocol_item in study_protocol_items:
                        data_type = protocol_item['data_fields']['data-type']
                        if data_type not in datatypes_to_remove:
                            study_protocol_items_post_purge.append(protocol_item)
# If you want to add to debugging messages
#                            print(f"keep {data_type}")
#                        else:
#                            print(f"remove{data_type}")

                    children[study_protocol_index]['items'] = study_protocol_items_post_purge
                    if len(study_protocol_items_post_purge) == 0:
                        del children[study_protocol_index]
                        post_purge_length = -1
                    else:
                        children[study_protocol_index]['items'] = study_protocol_items_post_purge
                        post_purge_length = len(study_protocol_items_post_purge)

                    print(f"{f} {post_purge_length} {pre_purge_length}")
#                if ((args.exclude is True) and ((len(investigator.get("primaryProjects")) + len(investigator.get("investigatorProjects"))) == 0)):
#                    continue
                file_name = f"{args.output_folder}/{f}"
                with open(file_name, "w", encoding="utf-8") as json_out:
                    json.dump(project, json_out, indent=4)

    except Exception as e:
        print(f"[ERROR] Exception while reading through folder: {args.input_folder}")
        print(e)
'''
    datatypes = ['aa', 'clin:vitalsData', 'cbat:simon']
    for dt in datatypes:
        print (dt)
        if dt in datatypes_to_remove:
            print(f"Remove {dt}")
'''

def remove_projects_master(args: argparse.Namespace) -> None:
    if (args.investigator_json):
        remove_projects_from_investigators(args)
    else:
        print("remove_projects_master: did not recognize target object. Expected investigator_json flag")

def remove_datatypes_master(args: argparse.Namespace) -> None:
    if (args.project_json):
        remove_datatypes_from_projects(args)
    else:
        print("remove_datatypes_master: did not recognize target object. Expected project_json flag")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform file modifications")

    parser.add_argument('--remove_projects',   dest='remove_projects',   help='Remove projects from JSON or XML file',     action='store_true')
    parser.add_argument('--remove_datatypes',  dest='remove_datatypes',  help='Remove datatypes from JSON or XML file',    action='store_true')
    parser.add_argument('--investigator_json', dest='investigator_json', help="Extract investigator JSON",                 action='store_true')
    parser.add_argument('--project_json',      dest='project_json',      help="Extract project JSON",                      action='store_true')

    parser.add_argument('--exclude',           dest='exclude',           help="Exclude objects if all subobjects removed", action='store_true')

    parser.add_argument('--output_folder',     dest='output_folder',     help="Folder to store output JSON files")
    parser.add_argument('--input_folder',      dest='input_folder',      help='Input folder of JSON or XML files')
    parser.add_argument('--csv',               dest='csv_file',          help='Path to CSV file')


    args = parser.parse_args()


    if args.remove_projects:
        remove_projects_master(args)
    elif args.remove_datatypes:
        remove_datatypes_from_projects(args)
    else:
        print("[ERROR] No valid action specified.")


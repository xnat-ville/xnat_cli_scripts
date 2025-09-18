#!/bin/python3
"""
file_mods.py

"""

import argparse

import warnings
from pathlib import Path
from os import listdir
import xml.etree.ElementTree as ET
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

def whitelist_session_xml_assessor_datatypes(args: argparse.Namespace) -> None:
    print("whitelist_session_xml_assessor_datatypes")
    if (not args.input_file) and (not args.output_file):
        print(f"Missing --input_file and/or --output_file for whitelist_session_xml_assessor_datatypes {args}")
        exit(1)

    white_list = xnat_cli_scripts.cli_common.read_text_file_into_set(args.assessor_datatypes)
    try:
        session_tree = ET.parse(args.input_file)
        session_root = session_tree.getroot()
        element_count = len(session_root)

        assessors_to_remove = []

        assessor_elements = session_root.find('{http://nrg.wustl.edu/xnat}assessors')
        if assessor_elements is not None:
            index = 0
            assessor_count = len(assessor_elements)
            for assessor in assessor_elements.findall('{http://nrg.wustl.edu/xnat}assessor'):
                data_type = assessor.attrib['{http://www.w3.org/2001/XMLSchema-instance}type']
                assessor_id: str = assessor.attrib['ID']
                index += 1
                if data_type not in white_list:
                    print(f"Removing datatype {data_type}")
                    assessors_to_remove.append(assessor_id)
                else:
                    print(f"Retain {data_type}")

            # This next part is ugly. We read the XML line by line and then remove lines
            # that corresponds to the data types we have not whitelisted.
            # Wish we could have just done that with XML processing, but the library we chose
            # collapses name spaces. I did not want to alter the XNAT defined namespaces.
            raw_xml = xnat_cli_scripts.cli_common.read_text_file_into_list(args.input_file)

            data_types_removed = 0
            xml_length = len(raw_xml)
            last_assessor_close = -1
            for index in range(xml_length - 1, -1, -1):
                this_line = raw_xml[index]
                if '<!--hidden_fields' in this_line:
                    pass
                elif '</xnat:assessor>' in this_line:
                    # This is the closing line of an assessor. Store the index
                    # Ask we back over the lines in the file, we should find the first line in the assessor.
                    last_assessor_close = index
                else:
                    match = next((x for x in assessors_to_remove if x in this_line), False)
                    if match:
                        print(f"{index} {last_assessor_close} {this_line}")
                        del raw_xml[index:last_assessor_close]
                        last_assessor_close = -1

        with open(args.output_file, "w") as outfile:
            outfile.write("\n".join(raw_xml))
            outfile.close()

    except Exception as e:
        print(f"Exception for {args.input_file}")
        print(e)
        exit(1)

def whitelist_datatypes_master(args: argparse.Namespace) -> None:
    if (args.session_xml and args.assessor_datatypes):
        whitelist_session_xml_assessor_datatypes(args)
    else:
        print(f"Arguments are incomplete for the whitelist_datatypes request {args}")
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform file modifications")

    parser.add_argument('--remove_projects',     dest='remove_projects',     help='Remove projects from JSON or XML file',     action='store_true')
    parser.add_argument('--remove_datatypes',    dest='remove_datatypes',    help='Remove datatypes from JSON or XML file',    action='store_true')
    parser.add_argument('--whitelist_datatypes', dest='whitelist_datatypes', help='Whitelist/retain specific datatypes',       action='store_true')

    parser.add_argument('--investigator_json',   dest='investigator_json',   help="Extract investigator JSON",                 action='store_true')
    parser.add_argument('--project_json',        dest='project_json',        help="Extract project JSON",                      action='store_true')
    parser.add_argument('--session_xml',         dest='session_xml',         help="Apply operation to Session XML",            action='store_true')
    parser.add_argument('--assessor_datatypes',  dest='assessor_datatypes',  help="Path to Assessor datatypes to retain")

    parser.add_argument('--exclude',             dest='exclude',             help="Exclude objects if all subobjects removed", action='store_true')

    parser.add_argument('--output_folder',       dest='output_folder',       help="Folder to store output JSON files")
    parser.add_argument('--input_folder',        dest='input_folder',        help='Input folder of JSON or XML files')
    parser.add_argument('--csv',                 dest='csv_file',            help='Path to CSV file')
    parser.add_argument('--input_file',          dest='input_file',          help="Path to one input file")
    parser.add_argument('--output_file',         dest='output_file',         help="Pato to one output file")

    args = parser.parse_args()


    if args.remove_projects:
        remove_projects_master(args)
    elif args.remove_datatypes:
        remove_datatypes_from_projects(args)
    elif args.whitelist_datatypes:
        whitelist_datatypes_master(args)
    else:
        print("[ERROR] No valid action specified.")


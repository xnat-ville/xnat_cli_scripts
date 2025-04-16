#!/bin/python3
"""
projects.py
---
--------------------------------------------------------------------------------

This script interacts with a target XNAT instance to list and manage projects and users. 

Example usage:
    List all projects:
        python3 -m xnat_cli_scripts.projects -L

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
from os.path import isfile
#import xnat
#import xnat.core
import xnat.mixin
from xnat.session import XNATSession
from xnat.exceptions import XNATResponseError
import xnat_cli_scripts.cli_common


def apply_sleep(args: argparse.Namespace) -> None:
    """ Applies sleep if -s is specified """
    if args.sleep:
        try:
            sleep_time = float(args.sleep)
            if sleep_time > 0:
                time.sleep(sleep_time)
        except ValueError:
            print("[ERROR] Invalid sleep value. Please provide a valid number.")


def format_project_header_rows() -> str:
    return "ID\tName\tInsert Date\tSubject Count\tExperiment Count\tPI"
def format_project_data(project_json, project_object, args: argparse.Namespace) -> str:
    formatted_string=""
    if (args.brief_format is True):
        formatted_string = project_object.id
    elif (args.verbose is False):
        formatted_string = f"{project_object.id}\t{project_object.name}\t{len(project_object.subjects)}"
    else:
        pi_string = f"{project_json['pi_lastname']}, {project_json['pi_firstname']}"
        if (pi_string) == ", ":
            pi_string = "NONE"
        experiment_count = "Unknown"
        try:
            experiment_count = len(project_object.experiments)
        except KeyError:
            experiment_count = "Unknown"
        except requests.exceptions.ReadTimeout:
            experiment_count = "Unknown"

        formatted_string = f"{project_object.id}\t{project_object.name}\t{len(project_object.subjects)}\t{experiment_count}\t{pi_string}"

    return formatted_string

def format_project_id_name(p) -> str:
    return f"{p.id}, {p.name}"


def execute_list_projects(connection: XNATSession, args: argparse.Namespace) -> None:
    
    if args.csv_file:
        # Read project IDs from CSV file
        project_ids = []
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                project_ids.append(row[0])  # Assuming the project ID is in the first column

        # List only the projects from the CSV
        for project_id in project_ids:
            project_object = connection.projects.get(project_id)
            if project_object:
                print(format_project_data({}, project_object, args))
                # Apply sleep after processing each project
                apply_sleep(args)
    else:
        # List all projects as usual
        all_projects = connection.get_json(f"/data/projects")
        # Apply sleep after the REST call (moved up here)
        apply_sleep(args)

        result_set = all_projects['ResultSet']
        result = result_set['Result']

        for project_json in result:
            project_object = connection.projects[project_json['ID']]
            print(format_project_data(project_json, project_object, args))
            # Apply sleep after processing each project
            apply_sleep(args)


def execute_list_project_users(connection: XNATSession, args: argparse.Namespace) -> None:
    # Check if CSV file is provided
    if args.csv_file:  # Correctly reference args.csv_file
        # Read the CSV file and get the list of project IDs
        project_ids_from_csv = []
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row:  # Ensure that the row is not empty
                    project_ids_from_csv.append(row[0].strip())  # Append project IDs from CSV
    else:
        project_ids_from_csv = None

    all_projects = connection.get_json(f"/data/projects")
    # Apply sleep after the main REST call
    apply_sleep(args)

    result_set = all_projects['ResultSet']
    result = result_set['Result']

    for project_json in result:
        project_id = project_json['ID']

        # If CSV is provided, only process projects in the CSV file
        if project_ids_from_csv and project_id not in project_ids_from_csv:
            continue

        users = connection.get_json(f"/data/projects/{project_id}/users")
        # Apply sleep after fetching users for each project
        apply_sleep(args)

        user_result_set = users['ResultSet']
        user_results = user_result_set['Result']

        for user in user_results:
            print(f"{project_id}\t{user['login']}")


def execute_list_project_groups(connection: XNATSession, args: argparse.Namespace) -> None:
    all_projects = connection.get_json(f"/data/projects")
    # Apply sleep after the main REST call
    apply_sleep(args)

    result_set = all_projects['ResultSet']
    result     = result_set['Result']

    # If a CSV file is provided, read the project IDs to limit the results
    if args.csv_file:
        project_ids = []
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                if row:  # Skip empty rows
                    project_ids.append(row[0].strip())  # Assuming the project ID is in the first column

        # Filter the results to only include the projects in the CSV
        result = [project for project in result if project['ID'] in project_ids]

    for project_json in result:
        project_id = project_json['ID']

        users = connection.get_json(f"/data/projects/{project_id}/users")
        # Apply sleep after fetching users for each project
        apply_sleep(args)

        user_result_set = users['ResultSet']
        user_results    = user_result_set['Result']

        for user in user_results:
            print(f"{project_id}\t{user['login']}\t{user['GROUP_ID']}")
        
def execute_list_anon_status(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Lists anonymization status for projects.
    Prints: project_id,true|false if an anonymization script exists.
    Output is printed to stdout (no file writing).
    """

    project_ids = []

    # Load project IDs from CSV if provided
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return

    # If no CSV, get all projects
    if not project_ids:
        all_projects = connection.get_json("/data/projects")
        if 'ResultSet' in all_projects and 'Result' in all_projects['ResultSet']:
            project_ids = [proj['ID'] for proj in all_projects['ResultSet']['Result']]
        else:
            print("[ERROR] Failed to retrieve projects.")
            return

    for project_id in project_ids:
        anon_url = f"/data/projects/{project_id}/config/anon"
        try:
            response = connection.get_json(anon_url)
            has_anon = "true" if response and isinstance(response, dict) else "false"
        except xnat.exceptions.XNATResponseError:
            has_anon = "false"
        except Exception as e:
            print(f"[ERROR] Unexpected error for {project_id}: {e}")
            has_anon = "false"

        print(f"{project_id},{has_anon}")


def execute_list_scan_types(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Lists scan types for projects.
    Output: project_id,scan_type — printed to stdout.
    If --csv_file is provided, only checks the listed projects.
    """

    project_ids = []

    # Load project IDs from CSV if provided
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except FileNotFoundError:
            print(f"[ERROR] CSV file '{args.csv_file}' not found.")
            return
        except Exception as e:
            print(f"[ERROR] Failed to read CSV file: {e}")
            return

    # If no CSV provided, get all project IDs from XNAT
    if not project_ids:
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [
                proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])
            ]
        except RequestException as e:
            print(f"[ERROR] Failed to fetch projects: {e}")
            return

    if not project_ids:
        print("[INFO] No projects found.")
        return

    # Print scan types (stdout)
    for project_id in project_ids:
        try:
            scan_types_response = connection.get_json(f"/data/projects/{project_id}/scan_types")
            scan_types = [
                item['type'] for item in scan_types_response.get('ResultSet', {}).get('Result', [])
            ]

            for scan_type in scan_types:
                print(f"{project_id},{scan_type}")

        except RequestException as e:
            print(f"[ERROR] Failed to fetch scan types for project '{project_id}': {e}")

def execute_list_prearchive_code(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Lists prearchive code for each project.
    Output format: {project_id}\t{prearchive_code}
    Printed to stdout. Shell script should redirect output.
    """

    project_ids = []

    # Load project IDs from CSV if provided
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Error reading CSV file: {e}")
            return

    # If no CSV, fetch all project IDs
    if not project_ids:
        all_projects = connection.get_json("/data/projects")
        if 'ResultSet' in all_projects and 'Result' in all_projects['ResultSet']:
            project_ids = [proj['ID'] for proj in all_projects['ResultSet']['Result']]
        else:
            print("[ERROR] Failed to retrieve projects.")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/prearchive_code")
            apply_sleep(args)

            if response.status_code == 200:
                prearchive_code = response.text.strip()
                print(f"{project_id}\t{prearchive_code}")
            else:
                print(f"{project_id}\tERROR\t{response.status_code}: {response.text}")
        except requests.RequestException as e:
            print(f"{project_id}\tERROR\tRequest failed: {e}")


def execute_remove_groups(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Remove groups specified in the CSV file.
    CSV Format: {project}{tab}{user}{tab}{group}
    Appends "REMOVED" or "ERROR" to each line.
    """

    if args.csv_file:
        groups_to_remove = []

        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                for row in csv_reader:
                    if len(row) < 3:
                        print(f"[ERROR] Invalid row format: {row}. Skipping.")
                        continue

                    project = row[0].strip()  # Project ID
                    user = row[1].strip()     # User
                    group = row[2].strip()    # Group to be removed
                    
                    groups_to_remove.append((project, user, group))

        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return

        # Iterate over each group and remove it
        for project, user, group in groups_to_remove:
            # Construct the URL for removing the group (same style as execute_update_groups)
            remove_url = f"/data/projects/{project}/users/{group}/{user}"

            try:
                # Use `connection.put()` instead of `requests.put()`
                response = connection.delete(remove_url)

                apply_sleep(args)  # Sleep after each API call

                if response.status_code == 200:
                    print(f"{project}\t{user}\t{group}\tREMOVED")
                else:
                    print(f"{project}\t{user}\t{group}\tERROR\t{response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"{project}\t{user}\t{group}\tERROR\tRequest failed: {e}")

def execute_update_groups(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Force update groups for users in the specified projects based on the CSV file.
    Uses XNATSession for authentication exactly like list_project_groups.

    CSV Format: {project_id}{tab}{user}{tab}{new_group}
    
    Echoes back the original input line and appends:
      - "CHANGED" if the request succeeds
      - "ERROR" if the request fails
    """
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                
                for row in csv_reader:
                    if len(row) < 3:
                        print(f"[ERROR] Invalid row format: {row}. Skipping.")
                        continue
                    
                    project_id, user, new_group = row[0].strip(), row[1].strip(), row[2].strip()

                    # Construct the URL for updating the group (relative path)
                    update_url = f"/data/projects/{project_id}/users/{new_group}/{user}"

                    # Use XNATSession for authentication, just like list_project_groups
                    response = connection.put(update_url)  

                    apply_sleep(args)  # Keeps delay between API calls

                    # Check response and print result
                    if response.status_code == 200:
                        print(f"{project_id}\t{user}\t{new_group}\tCHANGED")
                    else:
                        print(f"{project_id}\t{user}\t{new_group}\tERROR\t{response.status_code}: {response.text}")

        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")

def extract_most_recent_anonymization_script_configuration(anon_json: list):
    index = 0;
    candidate_index = int(0)
    first_result = anon_json[0]
    candidate_version = int(first_result['version'])
    for anon in anon_json:
        this_version = int(anon['version'])
        if (this_version >= candidate_version):
            candidate_version = this_version
            candidate_index = index
        index += 1

    selected_result = anon_json[candidate_index]
    return selected_result

def execute_update_anon_scripts_json(connection: XNATSession, args: argparse.Namespace) -> None:

    if args.input_folder is None:
        raise Exception("projects --update --anon requires --input_folder")

    project_ids = []
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return
    else:
        try:
            listing = listdir(args.input_folder)
            for f in listing:
                # File name should be something like Project_ID.anon.json
                id = f.split('.')[0]
                project_ids.append(id)
        except Exception as e:
            raise Exception(f"[ERROR] Exception while getting list of files in folder: {args.input_folder}\n{e}")

    print(f"Length of project_ids {len(project_ids)}")

    try:
        http_headers = {}
        http_headers['Content-Type'] = 'text/plain'
#        http_headers['Content-Type'] = 'application/json'
        project_count = len(project_ids)
        project_index = 1
        response = ""
        for id in project_ids:
            print(f"{project_index} / {project_count} / {id}.anon.json")
            project_index += 1
            if id.startswith("#"):
                continue

            upload_project_xml_template(connection, args, id)
            file_path=f"{args.input_folder}/{id}.anon.json"
            path_object = Path(file_path)
            if (not path_object.is_file()):
                continue
            print(f"Upload anonymization from {file_path}")
            anon_json = xnat_cli_scripts.cli_common.read_json_file(file_path)
            current_anon_script = extract_most_recent_anonymization_script_configuration(anon_json['ResultSet']['Result'])
            if (current_anon_script['status'] == "disabled"):
                continue
            anon_script_text = current_anon_script['contents']
#            status = anon_json['ResultSet']['Result'][0]['status']
#            if (status == "disabled"):
#                continue

#            anon_script = anon_json['ResultSet']['Result']
            put_path = f"/data/projects/{id}/config/anon/{id}"
            put_path = f"/xapi/anonymize/projects/{id}"

#            response = connection.put(put_path, data=str(current_anon_script), headers=http_headers)
#            response = connection.put(put_path, data=current_anon_script, headers=http_headers)
            if args.verbose:
                print(str(current_anon_script))
            response = connection.put(put_path, data=anon_script_text, headers=http_headers)


    except Exception as e:
        print(f"[ERROR] Exception when uploading to {put_path}")
        print(f"[ERROR] Exception while uploading anonymization script {file_path}\n{e}")



def execute_list_project_accessibilities(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Lists project accessibilities (private/public/protected).
    Output format: {project}{tab}{accessibility}.
    """
    project_ids_from_csv = None

    # If CSV file is specified, read project IDs from CSV
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids_from_csv = [row[0].strip() for row in csv_reader if row]  # Handle empty rows
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return

    # Get all projects using `connection`
    all_projects = connection.get_json("/data/projects")
    
    apply_sleep(args)  # Apply sleep after API call

    if 'ResultSet' not in all_projects or 'Result' not in all_projects['ResultSet']:
        print("[ERROR] Unexpected response format from /data/projects")
        return

    result = all_projects['ResultSet']['Result']

    for project_json in result:
        project_id = project_json.get('ID')
        if not project_id:
            print(f"[ERROR] Missing 'ID' for project: {project_json}")
            continue

        # If CSV is used, check if the project is in the CSV list
        if project_ids_from_csv and project_id not in project_ids_from_csv:
            continue

        # Use `connection.get()` instead of `requests.get()`
        accessibility_response = connection.get(f"/data/projects/{project_id}/accessibility")

        apply_sleep(args)  # Apply sleep after each REST call

        if accessibility_response.status_code == 200:
            accessibility = accessibility_response.text.strip()  # Ensure plain text handling (no JSON parsing)
        else:
            print(f"[ERROR] Failed to retrieve accessibility for {project_id}: {accessibility_response.status_code}")
            accessibility = "Unknown"

        # Print the project ID and its accessibility
        print(f"{project_id}\t{accessibility}")


def execute_list_project_configs(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Lists project configs.
    Output format: {project}{tab}{tool}.
    """
    project_ids_from_csv = None

    # If CSV file is specified, read project IDs from CSV
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids_from_csv = [row[0].strip() for row in csv_reader if row]  # Handle empty rows
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return

    # Get all projects using `connection`
    all_projects = connection.get_json("/data/projects")

    apply_sleep(args)  # Apply sleep after API call

    if 'ResultSet' not in all_projects or 'Result' not in all_projects['ResultSet']:
        print("[ERROR] Unexpected response format from /data/projects")
        return

    result = all_projects['ResultSet']['Result']

    for project_json in result:
        project_id = project_json.get('ID')
        if not project_id:
            print(f"[ERROR] Missing 'ID' for project: {project_json}")
            continue

        # If CSV is used, check if the project is in the CSV list
        if project_ids_from_csv and project_id not in project_ids_from_csv:
            continue

        try:
            configs_response = connection.get_json(f"/data/projects/{project_id}/config")
            configs = "XX"

            apply_sleep(args)  # Apply sleep after each REST call

            configs = configs_response['ResultSet']['Result']
            for config in configs:
                print(f"{project_id}\t{config['tool']}")
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue


def execute_update_accessibilities(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Update the accessibility of projects based on the CSV file.
    CSV Format: {project_id}{tab}{new_accessibility}
    The function directly updates the accessibility without checking the current state.
    Echoes back the original input line and appends "UPDATED" or "ERROR".
    """

    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                for row in csv_reader:
                    if len(row) < 2:
                        continue
                    
                    project_id, new_accessibility = row[0].strip(), row[1].strip().lower()

                    if new_accessibility not in ['private', 'public', 'protected']:
                        print(f"[ERROR] Invalid accessibility '{new_accessibility}' for project {project_id}. Skipping.")
                        continue

                    # Directly update the accessibility (no checking of current state)
                    endpoint = f"/data/projects/{project_id}/accessibility/{new_accessibility}"
                    response = connection.put(endpoint)

                    apply_sleep(args)  # Sleep after PUT call

                    if response.status_code == 200:
                        print(f"{project_id}\t{new_accessibility}\tUPDATED")
                    else:
                        print(f"{project_id}\t{new_accessibility}\tERROR\t{response.status_code}: {response.text}")

        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")

def upload_project_xml_template(connection: XNATSession, args: argparse.Namespace, project_id: str) -> None:
    if (args.template is None):
        return

    template_xml = xnat_cli_scripts.cli_common.read_text_file(args.template)
    project_xml  = template_xml.replace("PROJECT_ID", project_id)
    http_headers = {}
    http_headers['Content-Type'] = 'application/xml'
    put_path = f"/data/projects/{project_id}"

    # Let the function that called this trap the exception
    print(f"Upload template version of project XML: {put_path}")
    connection.put(put_path, data=project_xml, headers=http_headers)

def execute_update_project_xml(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Update/upload project XML by reading XML for individual files in an input folder.
    """

    if args.input_folder is None:
        raise Exception("projects --update --project_xml requires --input_folder")

    project_ids = []
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return
    else:
        try:
            listing = listdir(args.input_folder)
            for f in listing:
                # File name should be something like Project_ID.xml
                id = f.split('.')[0]
                project_ids.append(id)
        except Exception as e:
            raise Exception(f"[ERROR] Exception while getting list of files in folder: {args.input_folder}\n{e}")

    try:
        http_headers = {}
        http_headers['Content-Type'] = 'application/xml'
        project_count = len(project_ids)
        project_index = 1
        response = ""
        file_path="XX"
        for id in project_ids:
            if (not id.startswith("#")):
                upload_project_xml_template(connection, args, id)
                file_path=f"{args.input_folder}/{id}.xml"
                print(f"{project_index} / {project_count} / {id}.xml")
                with open(file_path) as xml_file:
                    put_path = f"/data/projects/{id}"
                    print(f"Upload project XML: {put_path}")
                    response=connection.put(put_path, data=xml_file, headers=http_headers)
                    xml_file.close()
            project_index += 1
    except Exception as e:
        print(f"[ERROR] Exception while uploading project XML: {file_path}.xml\n{e}")



def execute_update_tracer_json(connection, args):
    """
    Transfers tracer config from .tracer.json files by:
    1. Extracting all 'contents' fields
    2. Writing them to .tracer.txt in test_data/tracer_json/txt/
    3. PUTting that text to the destination XNAT instance
    """

    if not args.input_folder:
        print("[ERROR] --input_folder is required.")
        return

    # Set txt output folder path
    txt_folder = Path("test_data/tracer_json/txt")
    txt_folder.mkdir(parents=True, exist_ok=True)

    # Read .tracer.json files
    listing = os.listdir(args.input_folder)
    tracer_files = [f for f in listing if f.endswith(".tracer.json")]
    if not tracer_files:
        print("[INFO] No .tracer.json files found.")
        return

    had_error = False

    for filename in tracer_files:
        project_id = Path(filename).with_suffix('').with_suffix('').name
        full_json_path = Path(args.input_folder) / filename
        txt_output_path = txt_folder / f"{project_id}.tracer.txt"

        try:
            with open(full_json_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            results = content.get("ResultSet", {}).get("Result", [])
            tracer_lines = [entry.get("contents", "").strip() for entry in results if entry.get("contents", "").strip()]

            if not tracer_lines:
                print(f"[WARNING] No valid contents found in {filename}")
                had_error = True
                continue

            # Write the .tracer.txt file to the correct path
            with open(txt_output_path, "w", encoding="utf-8") as f_out:
                for line in tracer_lines:
                    f_out.write(line + "\n")

            # PUT request
            put_url = f"/data/projects/{project_id}/config/tracers/tracers"
            with open(txt_output_path, "r", encoding="utf-8") as f_txt:
                txt_data = f_txt.read()

            headers = {'Content-Type': 'text/plain'}
            response = connection.put(put_url, data=txt_data, headers=headers)

            if response.status_code not in [200, 201]:
                print(f"[ERROR] PUT failed for {project_id}: {response.status_code} {response.text}")
                had_error = True

        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")
            had_error = True

    if had_error:
        print("[ERROR] Tracer processing finished with some errors.")
    else:
        print("[INFO] All tracers have been updated successfully.")

def execute_list_master(connection: XNATSession, args: argparse.Namespace) -> None:
    
    if args.prearchive_code:
        execute_list_prearchive_code(connection, args)
    elif args.scan_types:
        execute_list_scan_types(connection, args)
    elif args.anon:
        execute_list_anon_status(connection, args)
    elif args.users:
        execute_list_project_users(connection, args)
    elif args.groups:
        execute_list_project_groups(connection, args)
    elif args.accessibilities:
        execute_list_project_accessibilities(connection, args)
    elif args.configs:
        execute_list_project_configs(connection, args)
    else:
        execute_list_projects(connection, args)

def execute_remove_master(connection: XNATSession, args: argparse.Namespace) -> None:
    if args.groups:
        execute_remove_groups(connection, args)

def execute_update_master(connection: XNATSession, args: argparse.Namespace) -> None:
    if args.groups:
        execute_update_groups(connection, args)
    elif args.anon:
        execute_update_anon_scripts_json(connection, args)
    elif args.accessibilities:
        execute_update_accessibilities(connection, args)
    elif args.project_xml:
        if args.input_folder:
            execute_update_project_xml(connection, args)
        else:
            print("[WARNING] No input folder provided for project XML update.")
    elif args.tracer_json:
        execute_update_tracer_json(connection, args)
    else:
        print("[WARNING] Invalid UPDATE action. Use --update with --accessibilities, --project_xml, --groups, or --tracer_json.")


def execute_get_project_xml(connection: XNATSession, args: argparse.Namespace) -> None:
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    project_ids = []
    if args.csv_file:
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                project_ids.append(row[0])  # Assuming the project ID is in the first column
    else:
        all_projects = connection.get_json(f"/data/projects")
        # Apply sleep after the REST call (moved up here)
        result = all_projects['ResultSet']['Result']

        for project_json in result:
            project_ids.append(project_json['ID'])

    project_count = len(project_ids)
    project_index = 1
    for id in project_ids:
        if args.verbose:
            print(f"{project_index} / {project_count} / {id}")
            project_index += 1

        xml=connection.get(f"/data/projects/{id}?format=xml")
        z = xml.content
        f=open(f"{args.output_folder}/{id}.xml", "w")
        f.write(xml.content.decode("utf-8"))
        f.close()

def execute_get_series_import_filter_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves the Series Import Filter for each project and saves it as a JSON file.
    """
    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)
    output_folder = args.output_folder

    project_ids = []
    if args.csv_file:
        with open(args.csv_file, mode='r') as file:
            project_ids = [row.strip() for row in file.readlines() if row.strip()]
    else:
        all_projects = connection.get_json("/data/projects")
        project_ids = [p['ID'] for p in all_projects['ResultSet']['Result']]

    for project_id in project_ids:
        sif_url = f"/data/projects/{project_id}/config/seriesImportFilter"

        try:
            response = connection.get_json(sif_url)
            if response:
                file_path = f"{output_folder}/{project_id}.seriesImportFilter.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(response, f, indent=4)
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue

    print("[INFO] Successfully saved Series Import Filters.")

def execute_get_anon_scripts_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves anonymization scripts from XNAT projects and saves them to an output folder.
    Only saves scripts for projects that have one enabled.
    If --csv is provided, only checks the listed projects.
    """
    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    # Get project IDs
    project_ids = []
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except Exception as e:
            print(f"[ERROR] Failed to read CSV file: {e}")
            return
    else:
        print("[INFO] No CSV file provided, attempting to retrieve anonymization scripts for all projects.")
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    # Fetch and save anonymization scripts
    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/config/anon")
            response.raise_for_status()

            script = response.json()
            if script:
                file_path = Path(args.output_folder) / f"{project_id}.anon.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(script, f, indent=4)

        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue
            print(f"[ERROR] Failed to retrieve anonymization script for project {project_id}: {e}")

    print("[INFO] Anonymization scripts retrieval completed.")

def execute_get_scan_types_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves scan types for each project and saves them as JSON files.
    Output filename: <projectID>.scan_types.json
    """
    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    # Load project IDs
    project_ids = []
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids = [row[0].strip() for row in csv_reader if row]
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}")
            return
    else:
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to fetch project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/scan_types")
            response.raise_for_status()
            scan_json = response.json()

            out_file = Path(args.output_folder) / f"{project_id}.scan_types.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(scan_json, f, indent=4)

        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue
            print(f"[ERROR] {project_id}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error for {project_id}: {e}")

    print("[INFO] Scan type JSON retrieval complete.")

def execute_get_tracer_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves tracer JSON exactly as returned by the server.
    Saves raw JSON content for each project as <projectID>.tracer.json.
    """

    if not args.output_folder:
        print("[ERROR] --output_folder is required for --get --tracer_json.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    project_ids = []

    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                project_ids = [line.strip() for line in file if line.strip()]
        except Exception as e:
            print(f"[ERROR] Failed to read CSV file: {e}")
            return
    else:
        try:
            response = connection.get_json("/data/projects")
            project_ids = [project['ID'] for project in response if 'ID' in project]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/config/tracers")
            output_file = Path(args.output_folder) / f"{project_id}.tracer.json"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.content.decode("utf-8"))

        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue
        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] Raw Tracer JSON retrieval complete.")

def execute_get_master(connection: XNATSession, args: argparse.Namespace) -> None:
    if args.project_xml:
        execute_get_project_xml(connection, args)
        return  

    if args.seriesImportFilter:
        execute_get_series_import_filter_json(connection, args)
        return

    if args.anon:
        execute_get_anon_scripts_json(connection, args)
        return

    if args.scan_types:
        execute_get_scan_types_json(connection, args)
        return

    if args.tracer_json:
        execute_get_tracer_json(connection, args)
        return

    print("[ERROR] No valid 'GET' action specified.")



#def execute_project_list(session: XNATSession, args: argparse.Namespace) -> None:
#
#    print(format_project_header_rows())
#    all_projects = session.get_json(f"/data/projects")
#
#    result_set = all_projects['ResultSet']
#    result     = result_set['Result']
#
#    for project_json in result:
#        project_object = session.projects[project_json['ID']]
#        project_id = project_json['ID']
#        project_name = project_json['name']
#        project_pi = f"{project_json['pi_lastname']}, {project_json['pi_firstname']}"
#        z = session.get_json(f"/data/projects/{project_id}")
#        print(format_project_data(project_json, project_object))


def format_subject_header_rows() -> str:
    return "Project ID, Project Label, ID, Label, Insert Date, Experiment Count"
def format_subject_data(p) -> str:
    return f"{p.id}, {p.label}, {p.insert_date}, {len(p.experiments)} "

def execute_subject_list(connection: XNATSession, args: argparse.Namespace) -> None:

    if (args.subjects):
        print("\nSubject List")
        print(format_subject_header_rows())
        for proj in connection.projects:
            project_header = format_project_id_name(connection.projects[proj])
            for subject in connection.projects[proj].subjects.values():
                print(f"{project_header}, {format_subject_data(subject)}")
                x = ""
                y = ""

def format_session_header_rows() -> str:
    return "Project ID, Project Label, ID, Label, Insert Date, Modality, Scan Count"
def format_session_data(p) -> str:
    return f"{p.id}, {p.label}, {p.insert_date}, {p.modality}, {len(p.scans)} "

def execute_session_list(connection: XNATSession, args: argparse.Namespace) -> None:

    if (args.sessions):
        print ("\nSession List")
        print(format_session_header_rows())
        for proj in connection.projects:
            po = connection.projects[proj]
            project_header = format_project_id_name(connection.projects[proj])
            for experiment in po.experiments.values():
                print(f"{project_header} {format_session_data(experiment)}")


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
    parser.add_argument('-u', '--users',           dest='users',                    help='Listing Verb object: Users',                 action='store_true')
    parser.add_argument('-g', '--groups',          dest='groups',                   help='Object: Groups (for both LIST and REMOVE)',  action='store_true')
    parser.add_argument(    '--seriesImportFilter',dest='seriesImportFilter',       help="Extract series import filter for projects",  action='store_true')
    parser.add_argument(      '--accessibilities', dest='accessibilities',          help="Accessibilities for projects",               action='store_true')
    parser.add_argument(      '--subjects',        dest='subjects',                 help="Include list of subjects in output",         action='store_true')
    parser.add_argument(      '--sessions',        dest='sessions',                 help="Include list of sessions in output",         action='store_true')
    parser.add_argument(      '--project_xml',     dest='project_xml',              help='Extract/Operate on Project XML',             action='store_true')
    parser.add_argument(      '--anon',            dest='anon',                     help="List anonymization status for projects",     action='store_true')
    parser.add_argument(      '--scan_types',      dest='scan_types',               help='List scan types',                            action='store_true')
    parser.add_argument(      '--prearchive_code', dest='prearchive_code',          help="List prearchive code for projects",          action='store_true')
    parser.add_argument(      '--tracer_json',     dest='tracer_json',              help="Retrieve tracer information for projects",   action='store_true')
    parser.add_argument(      '--configs',         dest='configs',                  help="Specify configs for list/get",               action='store_true')

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
    elif args.remove:
        execute_remove_master(session, args)
    elif args.update:
        execute_update_master(session, args)
    elif args.get:
        execute_get_master(session, args)
    else:
        print("[ERROR] No valid action specified. Use -L, -R, --update, or --get.")
finally:
    session.disconnect()  # Ensures cleanup even if an error occurs




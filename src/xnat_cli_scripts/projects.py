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
import xnat.mixin
from requests import RequestException
from xnat.session import XNATSession
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


def get_project_subject_ids(connection: XNATSession, args: argparse.Namespace) -> []:
    if (args.csv_file and args.csv_projects_subjects_file):
        raise Exception ("The variables ags.csv_file and args.csv_projects_subjects_file cannot both be populated")

    if args.csv_projects_subjects_file:
        project_subject_ids = []
        with open(args.csv_projects_subjects_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                if (not row[0].startswith("#")):
                    project_subject_ids.append(row)  # Assuming the project ID is in the first column
            file.close()
        return project_subject_ids

    project_subject_ids = []
    project_ids = get_project_ids(connection, args)
    project_count = len(project_ids)
    project_index = 1
    tab="\t"
    for project_id in project_ids:
        if args.verbose:
            xnat_cli_scripts.cli_common.print_stderr(f"{project_id}{tab}{project_index} / {project_count}")

        subject_ids = execute_get_subjects_list(connection, project_id)
        for subject_id in subject_ids:
            row = []
            row.append(project_id)
            row.append(subject_id)
            project_subject_ids.append(row)
        project_index += 1
    return project_subject_ids

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

    project_ids = get_project_ids(connection, args)

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

def find_most_recent_version(json_list: list) -> dict:
    if not json_list:
        return None
    return max(json_list, key=lambda item: int(item.get("version", 0)))

def execute_update_anon_scripts_json(connection: XNATSession, args: argparse.Namespace) -> None:

    # This is a PUT command for migration. It is not for manual updating of json files.

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
            results = anon_json.get('ResultSet', {}).get('Result', [])
            current_anon_script = find_most_recent_version(results)

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

def execute_update_prearchive_code(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Updates the prearchive code for each project using values from a CSV file.
    CSV Format: {project_id}\t{prearchive_code}
    """
    if not args.csv_file:
        print("[ERROR] --csv is required for --update --prearchive_code")
        return

    try:
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                if len(row) < 2:
                    print(f"[WARNING] Skipping invalid row: {row}")
                    continue

                project_id = row[0].strip()
                new_code = row[1].strip()

                url = f"/data/projects/{project_id}/prearchive_code/{new_code}"
                response = connection.put(url)

                apply_sleep(args)

                if response.status_code == 200:
                    print(f"{project_id}\t{new_code}\tUPDATED")
                else:
                    print(f"{project_id}\t{new_code}\tERROR\t{response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Failed to process CSV file: {e}")

def execute_update_bids_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    NOTE: May require BIDS plugin to be installed and properly configured.

    Updates the BIDS configuration for one or more XNAT projects. 

    Reads .bids.json files from the specified input folder. Each file should be named
    as <project_id>.bids.json and contain a valid JSON object representing the BIDS
    configuration for that project. Sends a PUT request to update the BIDS config via
    /data/projects/{project}/config/bids.

    Expects --input_folder and --csv flags to be provided.
    """

    if not args.input_folder:
        print("[ERROR]: --input_folder is required.")
        return

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
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        file_path = Path(args.input_folder) / f"{project_id}.bids.json"
        if not file_path.exists():
            print(f"[WARNING] No file found for {project_id}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                bids_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to parse {file_path}: {e}")
            continue

        try:
            response = connection.put(
                f"/data/projects/{project_id}/config/bids",
                json=bids_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            if response.status_code in [200, 201]:
                print(f"[SUCCESS] BIDS config updated for {project_id}")
            else:
                print(f"[ERROR] {project_id} failed: {response.status_code} {response.text}")
        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] BIDS update complete")

def execute_update_resource_config_json(connection: XNATSession, args: argparse.Namespace) -> None:
    if not args.input_folder:
        print("[ERROR] --input_folder is required.")
        return

    input_path = Path(args.input_folder)
    if not input_path.exists():
        print(f"[ERROR] Input folder does not exist: {args.input_folder}")
        return

    headers = {"Content-Type": "text/plain"}
    had_error = False

    for file in sorted(input_path.glob("*.resource_config.json")):
        project_id = file.stem.replace(".resource_config", "")
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            latest = find_most_recent_version(data.get("ResultSet", {}).get("Result", []))
            if not latest or not latest.get("contents"):
                print(f"[WARNING] No valid config contents found for {project_id}")
                had_error = True
                continue

            response = connection.put(
                f"/data/projects/{project_id}/config/resource_config",
                data=latest["contents"].strip(),
                headers=headers
            )
            if response.status_code in (200, 201, 204):
                print(f"[INFO] Updated resource_config for project: {project_id} (version {latest.get('version')})")
            else:
                print(f"[ERROR] Failed to update {project_id}: HTTP {response.status_code} {response.text}")
                had_error = True

        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")
            had_error = True

    if not had_error: 
        print("[INFO] Resource config JSON update complete.")

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
    This is a PUT command for migration. It is not for manual updating of json files.

    Transfers the most recent tracer config (by version) from .tracer.json files
    and PUTs that text to the destination XNAT instance.
    """

    if not args.input_folder:
        print("[ERROR] --input_folder is required.")
        return

    # Get tracer JSON files from input folder
    try:
        listing = os.listdir(args.input_folder)
        tracer_files = [f for f in listing if f.endswith(".tracer.json")]
    except Exception as e:
        print(f"[ERROR] Failed to list input folder: {e}")
        return

    if not tracer_files:
        print("[INFO] No .tracer.json files found.")
        return

    had_error = False
    headers = {'Content-Type': 'text/plain'}

    for filename in tracer_files:
        project_id = Path(filename).with_suffix('').with_suffix('').name
        full_path = Path(args.input_folder) / filename

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = data.get("ResultSet", {}).get("Result", [])
            latest_entry = find_most_recent_version(results)

            if not latest_entry:
                print(f"[WARNING] No valid tracer config found in {filename}")
                had_error = True
                continue

            tracer_text = latest_entry.get("contents", "").strip()
            if not tracer_text:
                print(f"[WARNING] Most recent tracer version for {project_id} has no contents.")
                had_error = True
                continue

            put_url = f"/data/projects/{project_id}/config/tracers/tracers"
            response = connection.put(put_url, data=tracer_text, headers=headers)

            if response.status_code not in [200, 201]:
                print(f"[ERROR] PUT failed for {project_id}: {response.status_code} {response.text}")
                had_error = True

        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")
            had_error = True

    if had_error:
        print("[ERROR] Tracer update completed with some errors.")
    else:
        print("[INFO] All tracers have been updated successfully.")

def execute_update_series_import_filter(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Migrates Series Import Filter config to destination XNAT without changing versioning or status.
    PUTs only the 'contents' from the latest version to the regular config endpoint.
    """

    if not args.input_folder:
        print("[ERROR] --input_folder is required for --update --seriesImportFilter")
        return

    try:
        files = [f for f in os.listdir(args.input_folder) if f.endswith(".seriesImportFilter.json")]
    except Exception as e:
        print(f"[ERROR] Failed to read input folder: {e}")
        return

    if not files:
        print("[INFO] No .seriesImportFilter.json files found.")
        return

    for filename in files:
        project_id = Path(filename).with_suffix('').with_suffix('').name
        full_path = Path(args.input_folder) / filename

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = data.get("ResultSet", {}).get("Result", [])
            latest = find_most_recent_version(results)

            if not latest:
                print(f"[WARNING] No valid version found in {filename}")
                continue

            contents = latest.get("contents", "").strip()
            if not contents:
                print(f"[WARNING] Skipping {project_id} due to empty contents.")
                continue

            put_url = f"/data/projects/{project_id}/config/seriesImportFilter"
            headers = {'Content-Type': 'text/plain'}

            response = connection.put(put_url, data=contents, headers=headers)

            if response.status_code in [200, 201]:
                print(f"[INFO] Copied series import filter for {project_id}")
            else:
                print(f"[ERROR] PUT failed for {project_id}: {response.status_code} {response.text}")

        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")

from urllib.parse import urlencode

def share_subjects_to_project(connection: XNATSession, shared_subjects: list) -> None:
    """
    Shares subjects from their original (primary) project into the current target project using XNAT's official sharing API.
    """
    for entry in shared_subjects:
        subject_id     = entry["id"]
        subject_label  = entry["label"]
        source_project = entry["source_project"]
        target_project = entry["target_project"]

        share_url = (
            f"/data/projects/{source_project}/subjects/{subject_id}/projects/{target_project}"
            f"?label={subject_label}"
        )

        try:
            response = connection.put(share_url)

            if response.status_code in [200, 201]:
                print(f"[SHARED] Subject {subject_label} ({subject_id}) shared from {source_project} to {target_project}")

            elif response.status_code == 409:
                print(f"[SKIP] Subject {subject_label} already shared with {target_project}")

            elif response.status_code == 403:
                print(f"[ERROR] 403 Forbidden — Check project permissions or source project mismatch for subject {subject_label}")

            elif response.status_code == 404:
                print(f"[ERROR] 404 Not Found — Subject {subject_id} or project may not exist")

            else:
                print(f"[ERROR] Sharing failed for {subject_label}: {response.status_code} {response.text}")

        except Exception as e:
            print(f"[ERROR] Exception while sharing subject {subject_label}: {e}")

def execute_update_subject_demographics_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Updates subject demographics in XNAT using bulk project JSON files.
    Pass 1: Update subjects that belong to the current project.
    Pass 2: Share subjects that originated from another project (shared subjects).
    """
    if not args.input_folder:
        print("[ERROR] --input_folder is required for --update --subjects")
        return

    try:
        files = [f for f in os.listdir(args.input_folder) if f.endswith(".json")]
    except Exception as e:
        print(f"[ERROR] Failed to read input folder: {e}")
        return

    if not files:
        print("[INFO] No .json files found.")
        return

    # Optional subject filter
    valid_subjects = None
    if args.csv_projects_subjects_file:
        try:
            valid_subjects = set()
            with open(args.csv_projects_subjects_file, mode='r') as file:
                reader = csv.reader(file, delimiter='\t')
                for row in reader:
                    if len(row) >= 2:
                        valid_subjects.add((row[0].strip(), row[1].strip()))
        except Exception as e:
            print(f"[ERROR] Failed to load subject filter CSV: {e}")
            return

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    shared_subjects = []

    for file in files:
        project_id = Path(file).stem
        file_path = Path(args.input_folder) / file

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                full_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON in {file_path}: {e}")
            continue

        subjects = full_data.get("ResultSet", {}).get("Result", [])
        if not subjects:
            print(f"[WARNING] No subjects found in {file_path}")
            continue

        for subj in subjects:
            subject_id = subj.get("ID")
            subject_label = subj.get("label")
            subject_project = subj.get("project")

            if not subject_id or not subject_project:
                print(f"[WARNING] Skipping malformed subject in {file_path}")
                continue

            # Check for shared subject
            if subject_project != project_id:
                print(f"[INFO] Skipping subject {subject_label} — was shared from project {subject_project} to {project_id}")
                shared_subjects.append({
                    "id": subject_id,
                    "label": subject_label,
                    "source_project": subject_project,
                    "target_project": project_id,
                    "json": subj
                })
                continue

            # Optional subject filter
            if valid_subjects and (subject_project, subject_id) not in valid_subjects:
                continue

            # Build query and PUT
            query_params = urlencode({key: str(value) for key, value in subj.items()})
            url = f"/data/archive/projects/{project_id}/subjects/{subject_id}?{query_params}"

            try:
                response = connection.put(url, json=subj, headers=headers)
                if response.status_code in [200, 201]:
                    print(f"[SUCCESS] {project_id}/{subject_label} updated.")
                elif response.status_code == 409:
                    print(f"[SKIP] {project_id}/{subject_label} already exists (conflict).")
                else:
                    print(f"[ERROR] {project_id}/{subject_label} failed: {response.status_code} {response.text}")
            except Exception as e:
                print(f"[ERROR] Exception uploading {project_id}/{subject_label}: {e}")

    # Second pass: share subjects
    if shared_subjects:
        print(f"[INFO] Starting second pass to share {len(shared_subjects)} shared subjects.")
        share_subjects_to_project(connection, shared_subjects)

    print("[INFO] Subject upload complete.")

def execute_update_downloader_json(connection: XNATSession, args: argparse.Namespace) -> None:
    if not args.input_folder:
        print("[ERROR] --input_folder is required.")
        return

    input_path = Path(args.input_folder)
    if not input_path.exists():
        print(f"[ERROR] Input folder does not exist: {args.input_folder}")
        return

    headers = {"Content-Type": "text/plain"}
    had_error = False

    for file in sorted(input_path.glob("*.downloader.json")):
        project_id = file.stem.replace(".downloader", "")
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            latest = find_most_recent_version(data.get("ResultSet", {}).get("Result", []))
            if not latest or not latest.get("contents"):
                print(f"[WARNING] No valid config contents found for {project_id}")
                had_error = True
                continue

            response = connection.put(
                f"/data/projects/{project_id}/config/downloader",
                data=latest["contents"].strip(),
                headers=headers
            )

            if response.status_code in (200, 201, 204):
                print(f"[INFO] Updated downloader config for project: {project_id} (version {latest.get('version')})")
            else:
                print(f"[ERROR] Failed to update {project_id}: HTTP {response.status_code} {response.text}")
                had_error = True

        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")
            had_error = True

    if not had_error:
        print("[INFO] Downloader config JSON update complete.")

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
    elif args.subjects and args.sessions:
        execute_list_subjects_sessions(connection, args)
    elif args.experiments:
        execute_list_experiments(connection, args)
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
    elif args.prearchive_code:
        execute_update_prearchive_code(connection, args)
    elif args.seriesImportFilter:
        execute_update_series_import_filter(connection, args)
    elif args.subject_demographics_json:
        execute_update_subject_demographics_json(connection, args)
    elif args.bids:
        execute_update_bids_json(connection, args)
    elif args.resource_config:
        execute_update_resource_config_json(connection, args)
    elif args.container_service:
        execute_update_container_service_json(connection, args)
    elif args.downloader:
        execute_update_downloader_json(connection, args)
    else:
        print("[WARNING] Invalid UPDATE action. Use --update with --accessibilities, --project_xml, --groups, or --tracer_json.")


def execute_get_complete_subject_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Fetches full JSON data for all subjects in each project.
    Saves one file per project: <project_id>.complete_subjects.json
    """
    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    output_dir = Path(args.output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    project_ids = get_project_ids(connection, args)
    project_count = len(project_ids)
    project_index = 1

    for project_id in project_ids:
        print(f"{project_index} / {project_count}  {project_id}")
        project_index += 1

        try:
            subjects = connection.projects[project_id].subjects.values()
            subject_json_list = []

            for subject in subjects:
                subj_data = connection.get_json(f"/data/subjects/{subject.id}")
                subject_json_list.append(subj_data)

            out_file = output_dir / f"{project_id}.complete_subjects.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"subjects": subject_json_list}, f, indent=4)

        except Exception as e:
            print(f"[ERROR] Failed to fetch/save subjects for {project_id}: {e}")

    print("[INFO] Complete subject JSON export finished.")


def execute_get_series_import_filter_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves the Series Import Filter for each project and saves it as a JSON file.
    """
    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)
    output_folder = args.output_folder

    project_ids = get_project_ids(connection, args)

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

    project_ids = get_project_ids(connection, args)

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

def count_unique_projects(project_subject_ids: []) -> int:
    project_set = set()
    for row in project_subject_ids:
        project_set.add(row[0])

    return len(project_set)

def execute_get_project_json(connection: XNATSession, args: argparse.Namespace) -> None:
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)
    project_ids = get_project_ids(connection, args)
    project_count = len(project_ids)
    project_index = 1

    for id in project_ids:
        if args.verbose:
            print(f"{project_index} / {project_count} / {id}")
            project_index += 1

        project_json = connection.get_json(f"/data/projects/{id}")
        with open(f"{args.output_folder}/{id}.json", "w") as f:
            json.dump(project_json, f, indent=4)
            f.close()


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
        result = all_projects['ResultSet']['Result']
        for project_json in result:
            project_ids.append(project_json['ID'])

    project_count = len(project_ids)
    project_index = 1
    for id in project_ids:
        if args.verbose:
            print(f"{project_index} / {project_count} / {id}")
            project_index += 1

        xml = connection.get(f"/data/projects/{id}?format=xml")
        with open(f"{args.output_folder}/{id}.xml", "w") as f:
            f.write(xml.content.decode("utf-8"))

'''
        project_folder = Path(args.output_folder) / project_id
        project_folder.mkdir(parents=True, exist_ok=True)

        subject_file = project_folder / f"{subject_id}.subject.json"
        #print(subject_file)
        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if (subject_file.exists()):
            print(f"{time_stamp}    Subject file exists {subject_file}")
        else:
            print(f"{time_stamp}    Need to retrieve subject json {project_id}/{subject_id}")
            try:
                response = connection.get(f"/data/subjects/{subject_id}", format="json", timeout=300)
                subject_json = response.json()

                with open(subject_file, "w", encoding="utf-8") as f:
                    json.dump(subject_json, f, indent=4)
                    f.close()

            except Exception as e:
                print(f"[ERROR] Failed to fetch/save subject {subject_id} in project {project_id}: {e}")
'''
#    project_ids = get_project_ids(connection, args)
#
#    project_count = len(project_ids)
#    project_index = 1
#
#    for project_id in project_ids:
#        if args.verbose:
#            subject_count = 0
#            subject_index = 0
#
#            xnat_cli_scripts.cli_common.print_stderr(f"Project {project_id} / {project_index} / {project_count}   NA {subject_index} / {subject_count}")
#
#        project_folder = Path(args.output_folder) / project_id
#        project_folder.mkdir(parents=True, exist_ok=True)
#
#        try:
#            subject_list = connection.get_json(f"/data/projects/{project_id}/subjects")
#            subjects = subject_list.get('ResultSet', {}).get('Result', [])
#        except Exception as e:
#            print(f"[ERROR] Failed to fetch subjects for {project_id}: {e}")
#            continue  # Move on to the next project
#
#        subject_count = len(subjects)
#        subject_index = 1
#        for subject in subjects:
#            subject_id = subject.get('ID')
#            if args.verbose:
#                xnat_cli_scripts.cli_common.print_stderr(f"Project {project_id} / {project_index} / {project_count}   {subject_id} {subject_index} / {subject_count}")
#                subject_index += 1
#
#            if not subject_id or 'label' not in subject:
#                continue  # Skip malformed entries
#
#            try:
#                response = connection.get(f"/data/subjects/{subject_id}", format="json", timeout=300)
#                subject_json = response.json()
#
#                output_file = project_folder / f"{subject_id}.subject.json"
#                with open(output_file, "w", encoding="utf-8") as f:
#                    json.dump(subject_json, f, indent=4)
#
#            except Exception as e:
#                print(f"[ERROR] Failed to fetch/save subject {subject_id} in project {project_id}: {e}")
#
#        project_index += 1
#

# This ver

def execute_get_subject_demographics_json(connection: XNATSession, args: argparse.Namespace) -> None:
    # Check if output folder is provided
    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    demographics_folder = Path(args.output_folder)
    demographics_folder.mkdir(parents=True, exist_ok=True)
    query_dictionary={"columns": "label,project,gender,handedness,education,race,ethnicity,group,yob,dob,age,height,weight,src"}

    project_ids = get_project_ids(connection, args)
    project_count = len(project_ids)
    project_index = 1
    for project_id in project_ids:
        print(f"{project_index} / {project_count}   {project_id} ")
        project_index += 1

        subjects_json=connection.get_json(f"/data/projects/{project_id}/subjects", query=query_dictionary)
        subjects_file = demographics_folder/f"{project_id}.json"
        with open(subjects_file, "w", encoding="utf-8") as f:
            json.dump(subjects_json, f, indent=4)
            f.close()

def execute_get_resource_config(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves resource_config JSON for each project and saves it to an output folder.
    Output filename: <projectID>.resource_config.json
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
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/config/resource_config")
            if response.status_code == 200:
                json_data = response.json()
                out_path = Path(args.output_folder) / f"{project_id}.resource_config.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue  # Skip silently if resource_config does not exist
        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] Resource config JSON retrieval complete.")

def execute_update_container_service_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Updates container-service wrapper config for each wrapper in each JSON file.
    Each file should be named <project_id>.container_service.json and contain
    multiple wrapper entries in ResultSet > Result.
    """

    if not args.input_folder:
        print("[ERROR] --input_folder is required.")
        return

    input_path = Path(args.input_folder)
    if not input_path.exists():
        print(f"[ERROR] Input folder does not exist: {args.input_folder}")
        return

    headers = {"Content-Type": "text/plain"}

    for file in sorted(input_path.glob("*.container_service.json")):
        project_id = file.stem.replace(".container_service", "")
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            wrappers = data.get("ResultSet", {}).get("Result", [])
            for wrapper in wrappers:
                wrapper_path = wrapper.get("path")
                contents = wrapper.get("contents", "").strip()

                if not wrapper_path or not contents:
                    print(f"[WARNING] Skipping missing wrapper info in {project_id}")
                    continue

                response = connection.put(
                    f"/data/projects/{project_id}/config/container-service/{wrapper_path}",
                    data=contents,
                    headers=headers
                )

                if response.status_code in (200, 201, 204):
                    print(f"[INFO] Updated wrapper '{wrapper_path}' for project {project_id}")
                else:
                    print(f"[ERROR] {project_id}/{wrapper_path}: HTTP {response.status_code} {response.text}")

        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] Container-service wrapper update complete.")


def execute_get_session_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves session JSONs based on a list of ProjectID, SubjectID, SessionID from a CSV/TXT file.
    Saves each session JSON to test_data/session_json/{SessionID}.json
    """
    if not args.csv_file:
        print("[ERROR] --csv is required to get session JSONs.")
        return

    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    try:
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            session_entries = [row for row in csv_reader if row]
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return

    for row in session_entries:
        if len(row) < 3:
            continue  # skip invalid rows

        project_id, subject_id, session_id = row[0], row[1], row[2]

        try:
            response = connection.get(f"/data/experiments/{session_id}?format=json")
            response.raise_for_status()

            session_json = response.json()
            output_file = Path(args.output_folder) / f"{session_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(session_json, f, indent=4)

        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                pass  # skip missing sessions silently
            else:
                xnat_cli_scripts.cli_common.print_stderr(f"[ERROR]: Failed to retrieve session {session_id}: {e}")
        except Exception as e:
            xnat_cli_scripts.cli_common.print_stderr(f"[ERROR]: Unexpected error for session {session_id}: {e}")

    print("[INFO] Session JSON retrieval completed successfully.")

def execute_get_session_xml(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves session XMLs based on a list of ProjectID, SubjectID, SessionID from a CSV/TXT file.
    Saves each session XML to test_data/session_xml/{SessionID}.xml
    """
    if not args.csv_file:
        print("[ERROR] --csv is required to get session XMLs.")
        return

    if not args.output_folder:
        print("[ERROR] --output_folder is required.")
        return

    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    try:
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            session_entries = [row for row in csv_reader if row]
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return

    session_count = len(session_entries)
    session_index = 0
    for row in session_entries:
        session_index += 1
        if len(row) < 3:
            continue  # skip invalid rows

        project_id, subject_id, session_id = row[0], row[1], row[2]

        try:
            Path(args.output_folder, project_id).mkdir(parents=True, exist_ok=True)
            print(f"{session_index} / {session_count}  Project {project_id}  Subject {subject_id}  Session {session_id}  ")
            response = connection.get(f"/data/experiments/{session_id}?format=xml")
            response.raise_for_status()

#            output_file = Path(args.output_folder, project_id) / f"{session_id}.xml"
            output_file = Path(args.output_folder, project_id, f"{session_id}.xml")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.content.decode("utf-8"))

        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                pass  # skip missing sessions silently
            else:
                xnat_cli_scripts.cli_common.print_stderr(f"[ERROR]: Failed to retrieve session {session_id}: {e}")
        except Exception as e:
            xnat_cli_scripts.cli_common.print_stderr(f"[ERROR]: Unexpected error for session {session_id}: {e}")

    print("[INFO] Session XML retrieval completed successfully.")

def execute_get_bids_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves BIDS configuration JSON for each project and saves it to an output folder.
    Output filename: <projectID>.bids.json

    Uses /data/projects/{project}/config/bids
    """

    if not args.output_folder:
        print("[ERROR]: --output_folder is required.")
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
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/config/bids")
            if response.status_code == 200:
                json_data = response.json()
                out_path = Path(args.output_folder) / f"{project_id}.bids.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue  # Skip if BIDS config doesn't exist
        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] BIDS JSON retrieval complete")

def execute_get_container_service_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves container_service JSON for each project and saves it to an output folder.
    Output filename: <projectID>.container_service.json
    """

    if not args.output_folder:
        print("[ERROR]: --output_folder is required.")
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
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/config/container-service")
            if response.status_code == 200:
                json_data = response.json()
                out_path = Path(args.output_folder) / f"{project_id}.container_service.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue # Skip silently if container_service does not exist
        except Exception as e:
            print (F"[ERROR] {project_id}: {e}")

    print("[INFO] Service container JSON retrieval complete")

def execute_get_project_resources_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves project-level resource metadata JSON for each project and saves it to an output folder.
    Output filename: <projectID>.resources.json

    Uses /data/projects/{project}/resources?format=json
    """

    if not args.output_folder:
        print("[ERROR]: --output_folder is required.")
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
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/resources?format=json")
            if response.status_code == 200:
                json_data = response.json()
                out_path = Path(args.output_folder) / f"{project_id}.resources.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue  # Skip if resources not found
        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] Project resources JSON retrieval complete")

def execute_get_downloader_config_json(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves downloader configuration JSON for each project and saves it to an output folder.
    Output filename: <projectID>.downloader.json

    Uses /data/projects/{project}/config/downloader
    """
    if not args.output_folder:
        print("[ERROR]: --output_folder is required.")
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
        try:
            all_projects = connection.get_json("/data/projects")
            project_ids = [proj['ID'] for proj in all_projects.get('ResultSet', {}).get('Result', [])]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve project list: {e}")
            return

    for project_id in project_ids:
        try:
            response = connection.get(f"/data/projects/{project_id}/config/downloader")
            if response.status_code == 200:
                json_data = response.json()
                out_path = Path(args.output_folder) / f"{project_id}.downloader.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
        except xnat.exceptions.XNATResponseError as e:
            if "404" in str(e):
                continue  # Downloader config might not exist
        except Exception as e:
            print(f"[ERROR] {project_id}: {e}")

    print("[INFO] Downloader JSON retrieval complete")

def execute_get_master(connection: XNATSession, args: argparse.Namespace) -> None:
    if args.subject_demographics_json:
        execute_get_subject_demographics_json(connection, args)
        return

    if args.complete_subject_json:
        execute_get_complete_subject_json(connection, args)
        return

    if args.project_xml:
        execute_get_project_xml(connection, args)
        return

    if args.project_json:
        execute_get_project_json(connection, args)
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

    if args.resource_config:
        execute_get_resource_config(connection, args)
        return

    if args.container_service:
        execute_get_container_service_json(connection, args)
        return

    if args.session_json:
        execute_get_session_json(connection, args)
        return

    if args.session_xml:
        execute_get_session_xml(connection, args)
        return

    if args.bids:
        execute_get_bids_json(connection, args)
        return

    if args.project_resources:
        execute_get_project_resources_json(connection, args)
        return

    if args.downloader:
        execute_get_downloader_config_json(connection, args)
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

def execute_list_subjects_sessions(connection: XNATSession, args: argparse.Namespace) -> None:
    project_ids = get_project_ids(connection, args)
    tab="\t"
    project_index = 1
    project_count = len(project_ids)
    for id in project_ids:
        po = connection.projects[id]
        subject_count = len(po.subjects)
        if args.verbose:
            xnat_cli_scripts.cli_common.print_stderr(f"Project {id} / {project_index} / {project_count} Subjects: {subject_count}")

        subject_index = 1
        for subject in po.subjects.values():
            if args.verbose:
                xnat_cli_scripts.cli_common.print_stderr(f"{id}{tab}{subject.id}  {subject_index} / {subject_count}   {project_index} / {project_count}")
            try:
                for experiment in subject.experiments:
#                    exp_path = f"/data/projects/{id}/subjects/{subject}/experiments/{experiment}"
#                    exp_path = f"/data/experiments/{experiment}"
#                    exp_json = connection.get_json(exp_path)
#                    data_type=exp_json['items'][0]['meta']['xsi:type']
                    print(f"{id}{tab}{subject.id}{tab}{experiment}")
#                    print(f"{id}{tab}{subject.id}{tab}{experiment}{tab}{exp.__xsi_type__}")
            except Exception as e:
                xnat_cli_scripts.cli_common.print_stderr(f"[ERROR] Exception for project {id} subject {subject.id}: {e}")
            subject_index += 1

        project_index += 1

def execute_list_experiments(connection: XNATSession, args: argparse.Namespace):
    project_ids = get_project_ids(connection, args)
    tab = "\t"
    project_index = 1
    project_count = len(project_ids)
    for project_id in project_ids:
        experiments = connection.get_json(f"/data/projects/{project_id}/experiments")
        for experiment in experiments['ResultSet']['Result']:
            print(f"{project_id}{tab}{experiment['label']}{tab}{experiment['ID']}")


def execute_get_subjects_list(connection: XNATSession, project_id: str) -> [] :
    subjects_list = []
    project_object = connection.projects[project_id]
    for subject in project_object.subjects.values():
        subjects_list.append(subject.id)

    return subjects_list

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
    parser.add_argument(      '--subjects',        dest='subjects',                 help='Include list of subjects in output',         action='store_true')
    parser.add_argument(   '--subject_demographics_json', dest='subject_demographics_json',  help='Operation includes subject XML',    action='store_true')
    parser.add_argument(    '--seriesImportFilter',dest='seriesImportFilter',       help="Extract series import filter for projects",  action='store_true')
    parser.add_argument(      '--accessibilities', dest='accessibilities',          help="Accessibilities for projects",               action='store_true')
    parser.add_argument(      '--sessions',        dest='sessions',                 help="Include list of sessions in output",         action='store_true')
    parser.add_argument(      '--project_xml',     dest='project_xml',              help='Extract/Operate on Project XML',             action='store_true')
    parser.add_argument(      '--project_json',    dest='project_json',             help='Extract/Operate on Project JSON',            action='store_true')
    parser.add_argument(      '--anon',            dest='anon',                     help="List anonymization status for projects",     action='store_true')
    parser.add_argument(      '--scan_types',      dest='scan_types',               help='List scan types',                            action='store_true')
    parser.add_argument(      '--prearchive_code', dest='prearchive_code',          help="List prearchive code for projects",          action='store_true')
    parser.add_argument(      '--tracer_json',     dest='tracer_json',              help="Retrieve tracer information for projects",   action='store_true')
    parser.add_argument(      '--configs',         dest='configs',                  help="Specify configs for list/get",               action='store_true')
    parser.add_argument(      '--resource_config', dest='resource_config',          help="Retrieve resource_config for projects",      action='store_true')
    parser.add_argument(      '--project_resources', dest='project_resources',                 help="Any resources at project level",            action='store_true')
    parser.add_argument(      '--container_service',dest='container_service',       help="Retrieve container_service for projects",    action='store_true')
    parser.add_argument(       '--complete_subject_json',dest='complete_subject_json',help="Retrieve entire subject JSONs by session ID",        action='store_true')
    parser.add_argument(       '--session_json',   dest='session_json',             help="Retrieve session JSONs by session ID",       action='store_true')
    parser.add_argument(       '--session_xml',    dest='session_xml',              help="Retrieve session XML files by session ID",   action='store_true')
    parser.add_argument(       '--experiments',    dest='experiments',              help="Include experiments in output list",         action='store_true')
    parser.add_argument(       '--bids',           dest='bids',                     help="Interacts with XNAT BIDS configuration",     action='store_true')
    parser.add_argument(       '--downloader',     dest='downloader',               help= "Interacts with XNAT downloader configuration", action='store_true')

    ## Further modifiers
    parser.add_argument('-b', '--brief',           dest='brief_format',             help="List in brief format",                       action='store_true')
    parser.add_argument('-s', '--sleep',           dest='sleep',                    help="Time to sleep after each REST call")
    parser.add_argument('-v', '--verbose',         dest='verbose',                  help="Verbose mode",                               action='store_true')
    parser.add_argument(      '--csv',             dest='csv_file',                 help='Path to CSV file operations such as listing, removing, or changing groups')
    parser.add_argument(  '--csv_projects_subjects', dest='csv_projects_subjects_file',  help="Path to CSV with project/subject ID tuplets")
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




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
import warnings
from pathlib import Path
from os import listdir
from os.path import isfile
#import xnat
#import xnat.core
import xnat.mixin
from xnat.session import XNATSession
import xnat_cli_scripts.cli_common
warnings.filterwarnings('ignore')


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
    return "ID\tName\tInsert Date\tSubject Count\tExperiment Count\PI"
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


def execute_list_projects(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    
    if args.csv_file:
        # Read project IDs from CSV file
        project_ids = []
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                project_ids.append(row[0])  # Assuming the project ID is in the first column

        # List only the projects from the CSV
        for project_id in project_ids:
            project_object = session.projects.get(project_id)
            if project_object:
                print(format_project_data({}, project_object, args))
                # Apply sleep after processing each project
                apply_sleep(args)
    else:
        # List all projects as usual
        all_projects = session.get_json(f"/data/projects")
        # Apply sleep after the REST call (moved up here)
        apply_sleep(args)

        result_set = all_projects['ResultSet']
        result = result_set['Result']

        for project_json in result:
            project_object = session.projects[project_json['ID']]
            print(format_project_data(project_json, project_object, args))
            # Apply sleep after processing each project
            apply_sleep(args)


def execute_list_project_users(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
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

    all_projects = session.get_json(f"/data/projects")
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
        
        # Apply sleep after processing each project's users
        apply_sleep(args)


def execute_list_project_groups(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    all_projects = session.get_json(f"/data/projects")
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
        
        # Apply sleep after processing each project's groups
        apply_sleep(args)


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


def execute_update_project_xml(connection: XNATSession, args: argparse.Namespace) -> None:
    """
    Update/upload project XML by reading XML for individual files in an input folder.
    """

    if args.input_folder:
        try:
            http_headers = {}
            http_headers['Content-Type: '] = 'application/xml'
            listing = listdir(args.input_folder)
            for f in listing:
                project_xml = xnat_cli_scripts.cli_common.read_text_file(f"{args.input_folder}/{f}")
                ab=project_xml
                tmp_string = str(Path(f).with_suffix(''))
                xnat_path=f"/data/archive/projects/{tmp_string}"
                # Do not have the right syntax yet
#                response = connection.put(xnat_path, data=project_xml, format="inbody=true" )

        except Exception as e:
            print(f"[ERROR] Exception while reading through folder: {args.input_folder}")


def execute_list_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    # Check for LIST actions first
    if args.users:
        execute_list_project_users(connection, args)
    elif args.groups:
        execute_list_project_groups(connection, args)
    elif args.accessibilities:
        execute_list_project_accessibilities(connection, args)
    else:
        execute_list_projects(connection, args)


def execute_remove_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    # Check for REMOVE action
    if args.remove and args.groups:
        # If CSV is provided, use it to get groups for removal
        if args.csv_file:
            execute_remove_groups(connection, args)
        else:
            print("[WARNING] No CSV file provided. Please specify --csv for group removal.")
    else:
        print("[WARNING] Invalid REMOVE action. Use -R with -g and --csv.")


def execute_update_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    # Check for UPDATE action (Change Groups)
    if args.update and args.groups:
        # If CSV is provided, use it for changing groups
        if args.csv_file:
            execute_update_groups(connection, args)
        else:
            print("[WARNING] No CSV file provided. Please specify --csv for changing groups.")
        return  # Exit after changing groups

    # Check for UPDATE action (Update Accessibilities)
    if args.update and args.accessibilities:
        # If CSV is provided, use it for updating accessibilities
        if args.csv_file:
            execute_update_accessibilities(connection, args)
        else:
            print("[WARNING] No CSV file provided. Please specify --csv for updating accessibilities.")
        return

    # Check for UPDATE action (Update Project XML)
    if args.update and args.project_xml:
        if args.input_folder:
            execute_update_project_xml(connection, args)
        else:
            print("[WARNING] No CSV file provided. Please specify --csv for updating project_xml.")
    else:
        print("[WARNING] Invalid UPDATE action. Use --update with --accessibilities, --project_xml or -g and --csv.")

def execute_get_project_xml(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    project_ids = []
    if args.csv_file:
        with open(args.csv_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter='\t')
            for row in csv_reader:
                project_ids.append(row[0])  # Assuming the project ID is in the first column
    else:
        all_projects = session.get_json(f"/data/projects")
        # Apply sleep after the REST call (moved up here)
        result = all_projects['ResultSet']['Result']

        for project_json in result:
            project_ids.append(project_json['ID'])


    for id in project_ids:
        xml=session.get(f"/data/projects/{id}?format=xml")
        z = xml.content
        f=open(f"{args.output_folder}/{id}.xml", "w")
        f.write(xml.content.decode("utf-8"))
        f.close()

def execute_get_series_import_filter(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    """
    Retrieves series import filter configuration for each project and saves it as a JSON file.
    The output is saved as: <output_folder>/<project ID>.seriesImportFilter.json
    """

    # Ensure the output directory exists
    Path(args.output_folder).mkdir(parents=True, exist_ok=True)

    # Retrieve all projects
    all_projects = connection.get_json("/data/projects")
    apply_sleep(args)

    if not all_projects or 'ResultSet' not in all_projects or 'Result' not in all_projects['ResultSet']:
        print("[ERROR] Failed to retrieve project list.")
        return

    project_list = all_projects['ResultSet']['Result']

    # If CSV file is provided, filter projects based on it
    project_ids_from_csv = None
    if args.csv_file:
        try:
            with open(args.csv_file, mode='r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                project_ids_from_csv = [row[0].strip() for row in csv_reader if row]
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {args.csv_file}")
            return
        except Exception as e:
            print(f"[ERROR] Exception while reading CSV: {e}")
            return

        # Filter the project list to only include those in the CSV file
        project_list = [p for p in project_list if p['ID'] in project_ids_from_csv]

    saved_count = 0
    not_found = []

    # Fetch and save Series Import Filter for each project
    for project in project_list:
        project_id = project['ID']
        sif_url = f"/data/projects/{project_id}/config/seriesImportFilter"

        response = connection.get_json(sif_url)
        apply_sleep(args)

        if response:
            output_file = f"{args.output_folder}/{project_id}.seriesImportFilter.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response, f, indent=4)
            saved_count += 1
        else:
            not_found.append(project_id)

    # Final print statement summarizing results
    print(f"[INFO] Successfully saved {saved_count} series import filter files.")
    
    if not_found:
        print(f"[WARNING] No series import filter found for {len(not_found)} projects: {', '.join(not_found)}")

def execute_get_master(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:
    """
    Master function to handle different 'GET' operations.
    """

    if args.get:
        if args.project_xml:
            if args.output_folder:
                execute_get_project_xml(connection, args)
            else:
                print("[WARNING] No output folder provided. Please specify --output_folder.")
            return

        elif args.seriesImportFilter:
            if args.output_folder:
                execute_get_series_import_filter(connection, args)
            else:
                print("[WARNING] No output folder provided. Please specify --output_folder.")
            return

    print("[ERROR] No valid 'GET' action specified. Use --project_xml or --seriesImportFilter.")

#def execute_project_list(session: xnat.session.XNATSession, args: argparse.Namespace) -> None:
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

def execute_subject_list(session: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    if (args.subjects):
        print("\nSubject List")
        print(format_subject_header_rows())
        for proj in session.projects:
            project_header = format_project_id_name(session.projects[proj])
            for subject in session.projects[proj].subjects.values():
                print(f"{project_header}, {format_subject_data(subject)}")
                x = ""
                y = ""

def format_session_header_rows() -> str:
    return "Project ID, Project Label, ID, Label, Insert Date, Modality, Scan Count"
def format_session_data(p) -> str:
    return f"{p.id}, {p.label}, {p.insert_date}, {p.modality}, {len(p.scans)} "

def execute_session_list(session: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    if (args.sessions):
        print ("\nSession List")
        print(format_session_header_rows())
        for proj in session.projects:
            po = session.projects[proj]
            project_header = format_project_id_name(session.projects[proj])
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

    ## Further modifiers
    parser.add_argument('-b', '--brief',           dest='brief_format',             help="List in brief format",                       action='store_true')
    parser.add_argument('-s', '--sleep',           dest='sleep',                    help="Time to sleep after each REST call")
    parser.add_argument('-v', '--verbose',         dest='verbose',                  help="Verbose mode",                               action='store_true')
    parser.add_argument('--csv',                   dest='csv_file',                 help='Path to CSV file operations such as listing, removing, or changing groups')
    parser.add_argument(      '--input_folder',    dest='input_folder',             help='Path to input folder of files')
    parser.add_argument(      '--output_folder',   dest='output_folder',            help='Path to output folder')

    args = parser.parse_args()

    args.url = "localhost:8080" if args.url is None else args.url

    auth_user = xnat_cli_scripts.cli_common.extract_auth_user(args)
    auth_password = xnat_cli_scripts.cli_common.extract_auth_password(args)
    xnat_extensions = xnat_cli_scripts.cli_common.extract_extension_types(args)

    session = xnat.connect(args.url, user=auth_user, password=auth_password, extension_types=xnat_extensions)

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

    session.disconnect()



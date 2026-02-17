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
import os

import xnat
import xnat.core
import xnat.mixin
from xnat.session import XNATSession

def format_project_header_rows() -> str:
    return "ID, Name, Insert Date, Subject Count, Experiment Count"
def format_project_data(p) -> str:
    formatted_string = f"{p.id}, {p.name}, {p.insert_date}, {len(p.subjects)}, {len(p.experiments)}"
    return formatted_string

def format_project_id_name(p) -> str:
    return f"{p.id}, {p.name}"

def execute_project_list(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    print(format_project_header_rows())
    for proj in connection.projects:
        y = connection.projects[proj]
        print(format_project_data(y))

def format_subject_header_rows() -> str:
    return "Project ID, Project Label, ID, Label, Insert Date, Experiment Count"
def format_subject_data(p) -> str:
    return f"{p.id}, {p.label}, {p.insert_date}, {len(p.experiments)} "

def execute_subject_list(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    if (args.subjects):
        print("\nSubject List")
        print(format_subject_header_rows())
        for proj in connection.projects:
            project_header = format_project_id_name(connection.projects[proj])
            for subject in connection.projects[proj].subjects.values():
                print(f"{project_header}, {format_subject_data(subject)}")
                x = ""
                y = ""



def format_session_header_rows(brief_format_flag) -> str:
    if brief_format_flag is not None and brief_format_flag is True:
        return "Project ID\tSession ID\tSession Label"
    else:
        return "Project ID\tSession ID\tSession Label\tInsert Date\tModality\tScan Count"


def format_session_data(project_id, p, brief_format_flag) -> str:
    if brief_format_flag is not None and brief_format_flag is True:
        return f"{project_id}\t{p.id}\t{p.label}\t "
    else:
        return f"{project_id}\t{p.id}\t{p.label}\t{p.insert_date}\t{p.modality}\t{len(p.scans)} "

def execute_session_list(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    if (args.csv_file is None):
        print ("\nSession List")
        print(format_session_header_rows(args.brief_format))
        for proj in connection.projects:
            if (args.project_id is None or args.project_id == proj):
                po = connection.projects[proj]
                for experiment_obj in po.experiments.values():
                    print(format_session_data(proj, experiment_obj, args.brief_format))
    else:
        print("\nSelected Sessions")
        print(format_session_header_rows(args.brief_format))
        with open(args.csv_file, newline='') as csvfile:
            rdr = csv.reader(csvfile, delimiter='\t')
            for row in rdr:
                experiment_obj = connection.create_object(f"/data/projects/{row[0]}/experiments/{row[1]}")
                print(format_session_data(row[0], experiment_obj, args.brief_format))
#                print(f"{row[0]}\t{row[1]}\t{experiment_obj}\t{experiment_obj.id}")

def execute_session_delete(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    print("\nDelete Sessions")
    with open(args.csv_file, newline='') as csvfile:
        rdr = csv.reader(csvfile, delimiter='\t')
        for row in rdr:
            experiment_obj = connection.create_object(f"/data/projects/{row[0]}/experiments/{row[1]}")
            print(f"{row[0]}\t{row[1]}\t{experiment_obj}")
            experiment_obj.delete(remove_files=True)

def execute_session_rename(connection: xnat.session.XNATSession, args: argparse.Namespace) -> None:

    print("\nRename Sessions")
    with open(args.csv_file, newline='') as csvfile:
        rdr = csv.reader(csvfile, delimiter='\t')
        for row in rdr:
            experiment_obj = connection.create_object(f"/data/projects/{row[0]}/experiments/{row[1]}")
            subject_id = experiment_obj.subject_id
            experiment_id = experiment_obj.id
            query_arguments = {"label": row[2]}
            print(f"{row[0]}\t{row[1]}\t{row[2]}\t{experiment_obj} {query_arguments}")
            url_path=f"/REST/projects/{row[0]}/subjects/{subject_id}/experiments/{experiment_id}"
            print(f"{url_path} {query_arguments}")
            connection.put(url_path, query=query_arguments)

def execute_are_present(connection: XNATSession, args: argparse.Namespace) -> None:
    test_experiments = create_experiment_dictionary(args.test_experiments)
    reference_experiments = create_experiment_dictionary(args.reference_experiments)
    reference_keys = reference_experiments.keys()
    count_missing = 0
    count_not_equal = 0
    total_values=len(reference_keys)
    missing_or_errant = []

    for k in reference_keys:
        reference_value = reference_experiments[k]
        if k in test_experiments and test_experiments[k] == reference_value:
            # All good
            pass
        elif k in test_experiments:
            print(f"Test value {test_experiments[k]} differs from {reference_experiments[k]} for {k}")
            missing_or_errant.append(k)
            count_not_equal += 1
        else:
            print(f"No test value present for {k}")
            missing_or_errant.append(k)
            count_missing += 1

    print(f"Missing {count_missing}, Not Equal {count_not_equal}, Total Keys {total_values}")
    if (args.csv_file):
        with open(args.csv_file, "w") as csv_output:
            for experiment in missing_or_errant:
                print(experiment, file=csv_output)



def execute_experiment_db_test(connection: XNATSession, args: argparse.Namespace) -> None:
    production_experiments = create_experiment_dictionary(args.production_exps)
    target_experiments = create_experiment_dictionary(args.target_exps)
    not_found_in_target = set()
    not_found_in_production = set()
    labels_differ = set()
    for k,v in production_experiments.items():
        if k in target_experiments:
            v_target = target_experiments[k]
            if v['label'] != v_target['label']:
                mashup=f"{k} / {v['label']} / {v_target['label']}"
                labels_differ.add(mashup)
        else:
            not_found_in_target.add(f"{v['insert_date_yyyy']} {v['project']} {k} {v['label']}")

    for k_target, v_target in target_experiments.items():
        if k_target not in production_experiments:
            not_found_in_production.add(f"{v_target['project']} {k_target} {v_target['label']} {v_target['insert_date_yyyymmdd']}")

    print(f"Production length:       {len(production_experiments)}")
    print(f"Target length:           {len(target_experiments)}")
    print(f"Not found in target:     {len(not_found_in_target)}")
    print(f"Not found in production: {len(not_found_in_production)}")
    print(f"Labels differ:           {len(labels_differ)}")

    if (args.output_folder):
        write_experiment_db_test_reports(args.output_folder, production_experiments, target_experiments, not_found_in_target, not_found_in_production, labels_differ)

    x = 3

def write_experiment_db_test_reports(report_folder:str, production_subjects:dict, target_subjects:dict, not_found_in_target:set, not_found_in_production:set, labels_differ:set) -> None:
    os.makedirs(report_folder, exist_ok=True)
    with open(f"{report_folder}/not_found_in_target.txt", 'w') as f:
        for v in sorted(not_found_in_target):
            print(v, file=f)

    with open(f"{report_folder}/not_found_in_production.txt", 'w') as f:
        for v in sorted(not_found_in_production):
            print(v, file=f)

    with open(f"{report_folder}/labels_differ.txt", 'w') as f:
        for v in sorted(labels_differ):
            print(v, file=f)

    print("Reports done")

def create_experiment_dictionary(file_path: str) -> dict:
    d = dict()
    with open(file_path, "r") as f:
        for experiment_line in f:
            experiment = dict()
            tokens = experiment_line.rstrip('\n').split('\t')
            experiment['project'] = tokens[0]
            experiment['id'] = tokens[1]
            experiment['label'] = tokens[2]
            experiment['insert_date'] = tokens[8]
            if tokens[9] != '':
                experiment['modified_date'] = tokens[9]
            else:
                experiment['modified_date'] = experiment['insert_date']

            insert_date_tokens = experiment['insert_date'].split(' ')
            experiment['insert_date_yyyymmdd'] = insert_date_tokens[0]
            insert_date_yyyymmdd = experiment['insert_date_yyyymmdd'].split('-')
            experiment['insert_date_yyyy'] = insert_date_yyyymmdd[0]

            experiment_key = experiment['id']
            if experiment_key in d:
                raise Exception(f"Duplicate Experiment ID: {experiment_key} current line: {experiment_line} existing record: {experiment}")
            d[experiment_key] = experiment

    return d




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List projects from an XNAT system")
    parser.add_argument(      '--no_xnat',         dest='no_xnat',         help='Do not make a connection to an XNAT',        action='store_true' )
    parser.add_argument('-x', '--xnat',            dest='url',             help="URL to XNAT, default is https://cnda.wustl.edu")
    parser.add_argument('-u', '--user',            dest='user',            help="User login for access to XNAT")

    # Commands
    parser.add_argument('-l', '--list',            dest='list_sessions',   help="Action is to LIST sessions",    action='store_true')
    parser.add_argument('-d', '--delete',          dest='delete_sessions', help="Action is to DELETE sessions",  action='store_true')
    parser.add_argument('-r', '--rename',          dest='rename_sessions', help="Action is to RENAME sessions",  action='store_true')
    parser.add_argument(      '--experiment_db_test', dest='experiment_db_test', help="Compare experiments in production/target DBs", action='store_true')

    # Command arguments
    parser.add_argument('-e', '--extension_types', dest='extension_types', help="True or False for extension_types in xnat.connect")
    parser.add_argument('-c', '--csv_file',        dest='csv_file',        help="CSV file with list of sessions for operations")
    parser.add_argument('-b', '--brief',           dest='brief_format',    help="List in brief format",          action='store_true')
    parser.add_argument('-p', '--project',         dest='project_id',      help="Optional Project ID used in list process")
    parser.add_argument(       '--target_exps',    dest='target_exps',     help="File with list of experiments in the target system")
    parser.add_argument(       '--production_exps',dest='production_exps', help="File with list of existing production experiments")

    parser.add_argument(      '--output_folder',   dest='output_folder',            help='Path to output folder')

    args = parser.parse_args()

    if (args.no_xnat):
        connection = None
    else:
        args.url = "https://cnda.wustl.edu" if args.url is None else args.url
        args.extension_types = False if args.extension_types is None else args.extension_types

        password = None
        args.extension_types = "True" if args.extension_types is None else args.extension_types
        connection = xnat.connect(args.url, user=args.user, password=password, extension_types=False)

    if args.list_sessions:
        execute_session_list(connection, args)
    elif args.delete_sessions:
        execute_session_delete(connection, args)
    elif args.rename_sessions:
        execute_session_rename(connection, args)
    elif args.experiment_db_test:
        execute_experiment_db_test(connection, args)
    else:
        print("Neighbor list nor delete specified on commandline")

    if connection:
        connection.disconnect()


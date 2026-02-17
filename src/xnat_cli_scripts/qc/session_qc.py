__version__ = (1, 0, 0)

import argparse
import csv
import os

def execute_session_archive_exists(args:argparse.Namespace) -> int:
    session_rows = read_csv_file(args.session_list)
    existing_session_folders = []
    missing_session_folders = []
    archive_base = args.archive_base
    for row in session_rows:
        project = row[0]
        session_id = row[1]
        session_label = row[2]
        session_folder = os.path.join(archive_base, project, "arc001", session_label)
        if os.path.isdir(session_folder):
            existing_session_folders.append(row)
        else:
            missing_session_folders.append(row)

    os.makedirs(args.output_folder, exist_ok=True)
    write_array_to_file(os.path.join(args.output_folder, "existing_session_folders.txt"), existing_session_folders)
    write_array_to_file(os.path.join(args.output_folder,  "missing_session_folders.txt"), missing_session_folders)



def read_csv_file(path:str) -> []:
    rows = []
    with open(path, newline='') as csvfile:
        rdr = csv.reader(csvfile, delimiter='\t')
        for row in rdr:
            rows.append(row)
    return rows

def write_array_to_file(path: str, rows:[]) -> None:
    with open(path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="XNAT Session QC Tasks")

    # Commands
    parser.add_argument('--session_archive_exists', dest='session_archive_exists',   help="Does the archive folder exist for listed sessions",    action='store_true')

    # Command arguments
    parser.add_argument('--archive_base',           dest='archive_base',             help="Base folder for XNT archive")
    parser.add_argument('--session_list',           dest='session_list',             help='List of sessions from database')
    parser.add_argument('--output_folder',          dest='output_folder',            help='Path to output folder')


    args = parser.parse_args()

    if args.session_archive_exists:
        execute_session_archive_exists(args)
    else:
        parser.print_usage()
        raise Exception("No recognized actions")




#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output file path

list_subjects_sessions() {
    export PYTHONPATH="$1/../src"

    echo "python3 -m xnat_cli_scripts.projects $2 --list --subjects --sessions > $3"
         python3 -m xnat_cli_scripts.projects $2 --list --subjects --sessions > $3
#         python3 -m xnat_cli_scripts.projects $2 --list --subjects --sessions
}

# Main starts here
# Arguments:
#               authentication string (user or user:password)
#               system (see common.sh)

if [ $# -lt 3 ]; then
    echo "Arguments: auth_string system active_projects_file [output file]"
    exit 1
fi

auth_string="$1"
system="$2"
active_projects="$3"
shift 3

BASE_FOLDER=$(dirname "$0")
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url "${system}")
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "
BOILER_PLATE=" -a $auth_string -x $url "
OUTPUT_FILE="test_data/subjects_sessions.txt"
if [[ $# -gt 0 ]] ; then
 OUTPUT_FILE="$1"
fi

# Run the prearchive code listing
list_subjects_sessions "$BASE_FOLDER" "$BOILER_PLATE --verbose --csv $active_projects " $OUTPUT_FILE


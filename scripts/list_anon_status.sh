#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output File Path

get_anon_status() {
    export PYTHONPATH="$1/../src"

    echo "Executing: python3 -m xnat_cli_scripts.projects $2 --list --anon > $3"
          python3 -m xnat_cli_scripts.projects $2 --list --anon > "$3"
}

# Main starts here
# Arguments:
#               authentication string (user or user:password)
#               system (see common.sh)

if [ $# -ne 2 ]; then
    echo "Arguments: auth_string system"
    exit 1
fi

auth_string="$1"
system="$2"

BASE_FOLDER=$(dirname "$0")
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url "${system}")
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "

# Run the anonymization status listing and redirect to the correct file
get_anon_status "$BASE_FOLDER" "$BOILER_PLATE" "test_data/anon_status.csv"


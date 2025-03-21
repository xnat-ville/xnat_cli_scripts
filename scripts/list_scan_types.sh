#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output file path

get_scan_types() {
    export PYTHONPATH="$1/../src"

    echo "Executing: python3 -m xnat_cli_scripts.projects $2 --list --scan_types --output_folder $3"
    python3 -m xnat_cli_scripts.projects $2 --list --scan_types --output_folder "$3"
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
url=$(get_xnat_url "$system")
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "

# Run the scan types listing
get_scan_types "$BASE_FOLDER" "$BOILER_PLATE" "test_data/scan_types.csv"

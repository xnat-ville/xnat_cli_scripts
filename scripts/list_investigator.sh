#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output File

list_investigators() {
    export PYTHONPATH="$1/../src"

    echo python3 -m xnat_cli_scripts.investigators $2 --list $3
         python3 -m xnat_cli_scripts.investigators $2 --list $3
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

BASE_FOLDER=`dirname $0`
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url ${system})
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "

list_investigators "$BASE_FOLDER" "$BOILER_PLATE" "test_data/investigators.txt"

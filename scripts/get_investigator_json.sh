#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output folder

get_investigator_json_files() {
    export PYTHONPATH="$1/../src"

    echo python3 -m xnat_cli_scripts.investigators $2 --get --investigator_json --output_folder $3 
         python3 -m xnat_cli_scripts.investigators $2 --get --investigator_json --output_folder $3
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

# Now, investigator JSON data will always go into 'test_data/investigator_json'
get_investigator_json_files "$BASE_FOLDER" "$BOILER_PLATE" "test_data/investigator_json"

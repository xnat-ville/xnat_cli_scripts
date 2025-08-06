#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Input folder

create_investigator_json_files() {
    export PYTHONPATH="$1/../src"

    echo python3 -m xnat_cli_scripts.investigators $2 --create --investigator_json --input_folder $3 
         python3 -m xnat_cli_scripts.investigators $2 --create --investigator_json --input_folder $3
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

echo Start $0 $* `date`

BASE_FOLDER=`dirname $0`
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url ${system})
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "


ls "test_data/modified_investigator_json" | sed -e 's/.json//' | sort -n > test_data/sorted_investigator_ids.txt
ls -l test_data/sorted_investigator_ids.txt

create_investigator_json_files "$BASE_FOLDER" "$BOILER_PLATE --csv test_data/sorted_investigator_ids.txt" "test_data/modified_investigator_json"

echo Complete $0 $* `date`

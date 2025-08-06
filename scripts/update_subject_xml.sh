#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Input folder

update_subject_xml() {
    export PYTHONPATH="$1/../src"

    echo python3 -m xnat_cli_scripts.projects $2 --update --subject_xml --input_folder $3
         python3 -m xnat_cli_scripts.projects $2 --update --subject_xml --input_folder $3
}

# Main starts here
# Arguments:
#               authentication string (user or user:password)
#               system (see common.sh)

if [ $# -ne 3 ]; then
    echo "Arguments: auth_string system active_projects_file"
    exit 1
fi

auth_string="$1"
system="$2"
active_projects="$3"

BASE_FOLDER=`dirname $0`
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url ${system})
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "

update_subject_xml	\
    "$BASE_FOLDER"	\
    "$BOILER_PLATE --csv $active_projects "	\
    test_data/subject_xml_processed

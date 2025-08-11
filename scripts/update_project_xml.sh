#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Input folder

update_project_xml() {
    export PYTHONPATH="$1/../src"

    echo python3 -m xnat_cli_scripts.projects $2 --update --project_xml --input_folder $3
         python3 -m xnat_cli_scripts.projects $2 --update --project_xml --input_folder $3
}

# Main starts here
# Arguments:
#               authentication string (user or user:password)
#               system (see common.sh)

if [ $# -ne 2 ]; then
    echo "Arguments: auth_string system"
    exit 1
fi

echo Start $0 $* `date`

auth_string="$1"
system="$2"

BASE_FOLDER=`dirname $0`
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url ${system})
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "

update_project_xml	\
    "$BASE_FOLDER"	\
    "$BOILER_PLATE --csv test_data/active_projects.txt --template templates/template_project_xml.xml"	\
    test_data/project_xml_processed

echo ""
echo Complete $0 $* `date`

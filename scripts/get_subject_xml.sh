#!/bin/bash

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output folder

get_subject_xml() {
    export PYTHONPATH="$1/../src"

    echo "python3 -m xnat_cli_scripts.projects $2 --get --subject_xml --output_folder $3"
          python3 -m xnat_cli_scripts.projects $2 --get --subject_xml --output_folder $3
}

# Main starts here
# Arguments:
#               authentication string (user or user:password)
#               system (see common.sh)

if [ $# -lt 2 ]; then
    echo "Arguments: auth_string system [project/subject list]"
    exit 1
fi

auth_string="$1"
system="$2"
shift 2

BASE_FOLDER=$(dirname "$0")
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url ${system})
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "
SUBJECTS_LIST=test_data/subjects.txt
if [ "$1" != "" ] ; then
  SUBJECTS_LIST="$1"
fi

echo Start get_subject_xml `date`

echo get_subject_xml "$BASE_FOLDER" "$BOILER_PLATE --csv $SUBJECTS_LIST" "test_data/subject_xml"
     get_subject_xml "$BASE_FOLDER" "$BOILER_PLATE --csv $SUBJECTS_LIST" "test_data/subject_xml"

echo Complete get_subject_xml `date`

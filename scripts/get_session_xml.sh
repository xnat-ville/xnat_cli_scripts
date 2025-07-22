#!/bin/bash

# Arguments
#              Input file of subjects/sessions (long file)
#              Output folder
#              File pattern for split command
my_split() {

  echo mkdir -p "$2"
       mkdir -p "$2"
 
  echo split -d -l 7000 $1 "$2/$3"
       split -d -l 7000 $1 "$2/$3"

  ls -lt $2

}

# Arguments:
#              Base Folder
#              Boiler Plate
#              Output folder
#              Log file

get_sessions() {
    export PYTHONPATH="$1/../src"

    echo "python3 -m xnat_cli_scripts.projects $2 --get --session_xml --output_folder $3  &> $4"
          python3 -m xnat_cli_scripts.projects $2 --get --session_xml --output_folder $3  &> $4
    sleep 15
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
shift 2

BASE_FOLDER=$(dirname "$0")
source "$BASE_FOLDER/common.sh"
set -e
url=$(get_xnat_url ${system})
set +e

BOILER_PLATE=" -a $auth_string -x $url -e False "

if [[ $# -ne 0 ]] ; then
 my_split test_data/subjects_sessions.txt test_data/splits subjs.sessions.
fi

log_folder=logs/get_session
mkdir -p $log_folder

rm -rf   test_data/session_xml
mkdir -p test_data/session_xml

ls test_data/splits

for split_file in test_data/splits/subjs.sessions.* ; do
  echo $split_file
  if [ -d $split_file ] ; then
    echo Skip folder $split_file
    continue
  fi

  echo $split_file
  base_name=`basename $split_file`
  log_file=logs/get_session/$base_name.log
  output_folder=test_data/session_xml/$base_name
  echo mkdir -p $output_folder
       mkdir -p $output_folder

  echo get_sessions "$BASE_FOLDER" "$BOILER_PLATE --sleep 1 --csv $split_file" "$output_folder" "$log_file"
       get_sessions "$BASE_FOLDER" "$BOILER_PLATE --sleep 1 --csv $split_file" "$output_folder" "$log_file"
done


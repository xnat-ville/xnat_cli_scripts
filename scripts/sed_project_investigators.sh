#!/bin/sh

sed_project_investigators() {
    export PYTHONPATH="$1/../src"

    echo python3 -m xnat_cli_scripts.file_mods --remove_projects --investigator_json --exclude $2
         python3 -m xnat_cli_scripts.file_mods --remove_projects --investigator_json --exclude $2
}


pre_flight() {
 for f in       \
        test_data/inactive_projects.txt ; do
  if [ ! -f $f ] ; then
   echo Required file is missing: $f
   echo Script will exit now
   exit 1
  fi
 done

 for f in       \
        test_data/investigator_json ; do
  if [ ! -d $f ] ; then
   echo Required folder is missing: $f
   echo Script will exit now
   exit 1
  fi
 done
}

pre_flight


BASE_FOLDER=`dirname $0`

sed_project_investigators "$BASE_FOLDER"			\
	"--input_folder test_data/investigator_json		\
	--output_folder test_data/modified_investigator_json	\
	--csv test_data/inactive_projects.txt "


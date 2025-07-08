#!/bin/bash

# Subroutine section

#$archive_folder $output_folder/archive_list.txt
generate_archive_list() {
 rm -f /tmp/sessions.$$.txt
 for project_path in $1/* ; do
  project_label=`basename $project_path`
  for session_path in $project_path/arc001/* ; do
   session_label=`basename $session_path`
   echo -e $project_label\\t$session_label >> /tmp/sessions.$$.txt
  done
 done

 
 sort /tmp/sessions.$$.txt > $2
 rm   /tmp/sessions.$$.txt
}

print_usage_and_die() {
 echo "Usage: session_list archive_folder output_folder"
 exit 1
}

check_arguments() {
 if [ $# -ne 3 ] ; then
  print_usage_and_die
 fi

 if [ ! -f "$1" ] ; then
  echo "Arg 1: $1 is not a file"
  print_usage_and_die
 fi

 if [ ! -e "$2" ] ; then
  echo "Arg 2: $2 does not exist"
  print_usage_and_die
 fi

 if [ ! -d "$2" ] ; then
  echo "Arg 2: $2 is not a folder"
  print_usage_and_die
 fi

 if [ -f "$3" ] ; then
  echo "Arg 3: $3 is a file when it should either be a folder or not exist yet"
  print_usage_and_die
 fi

}

# Main starts here

# Arguments:
#              Session List (Project_ID Session_Label Session_ID
#              Archive folder
#              Output folder

check_arguments $*

session_list="$1"
archive_folder="$2"
output_folder="$3"

archive_list="$output_folder/archive_list.txt"
sorted_sessions="$output_folder/session_list.txt"

mkdir -p $output_folder
sort $session_list > $sorted_sessions
echo Input $session_list sorted $sorted_sessions


generate_archive_list "$archive_folder" "$archive_list"
echo Archive list created $archive_list

grep    -f $output_folder/session_list.txt "$archive_list" > $output_folder/common.txt
echo Common folders/sessions created: $output_folder/common.txt

grep -v -f "$session_list" "$archive_list" > $output_folder/1-disk-only.txt
echo Diff 1 $output_folder/1-disk-only.txt

grep -v -f "$archive_list" "$session_list" > $output_folder/2-db-only.txt
echo Diff 2 $output_folder/2-db-only.txt

ls -lt $output_folder
wc -l $output_folder/common.txt $output_folder/?-*only.txt

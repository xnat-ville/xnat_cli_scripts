#!/bin/bash

# Args:
#       Session Label
#       Input XML
check_for_mismatch() {
 SESSION_LABEL=$1
    PROJECT_ID=`head -n 2 $2 | grep -o 'project=".*" label=' | sed -e 's/project=.//' -e 's/. label.$//'`
 SESSION_LABEL=`head -n 2 $2 | grep -o 'label=".*" xsi:sche' | sed -e 's/label=.//'   -e 's/" .*$//'`
 URI_LIST=`cat $2 |grep -o 'URI=.*catalog'`

 session_misplaced=0
 for URI in $URI_LIST; do
  SESSION_FOLDER=`echo $URI | grep -o 'arc001/.*/' | sed -e 's-arc001/--' -e 's-/.*--' `
  if [[ ${SESSION_LABEL} != ${SESSION_FOLDER} ]] ; then
   session_misplaced=1
  fi
 done
 echo $session_misplaced
}


TAB="	"
for folder in $* ; do
 echo $folder
 for f1 in $folder/* ; do
  echo $f1
  for project_folder in $f1 ; do
   echo $project_folder
   for session_xml in $project_folder/* ; do
    SESSION_LABEL=`head -n 2 $session_xml | grep -o 'label=".*" xsi:sche' | sed -e 's/label=.//'   -e 's/" .*$//'`
    flag=$( check_for_mismatch $SESSION_LABEL $session_xml )
    echo "$flag${TAB}$SESSION_LABEL${TAB}$session_xml"
   done
  done
 done
done

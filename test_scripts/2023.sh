#!/bin/bash

LABEL=2023

#echo ./scripts/list_subjects_sessions.sh smoore EXISTING test_data/active_projects.$LABEL.txt
#     ./scripts/list_subjects_sessions.sh smoore EXISTING test_data/active_projects.$LABEL.txt
#
#echo wc -l test_data/subjects_sessions.txt
#     wc -l test_data/subjects_sessions.txt
#
#if [[ -e test_data/splits/subjs.sessions.00 ]] ; then
# echo  rm test_data/splits/subjs.sessions.??
#       rm test_data/splits/subjs.sessions.??
#fi

echo cp -p test_data/subjects_sessions.txt test_data/splits/subjs.sessions.00
     cp -p test_data/subjects_sessions.txt test_data/splits/subjs.sessions.00

echo ls -lt test_data/splits
     ls -lt test_data/splits

echo ./scripts/get_session_xml.sh smoore EXISTING
     ./scripts/get_session_xml.sh smoore EXISTING

exit 0

echo "./scripts/find_orphan_session_folders.sh test_data/session_xml/subjs.sessions.00 > logs/session_consistency/$LABEL.txt"
      ./scripts/find_orphan_session_folders.sh test_data/session_xml/subjs.sessions.00 > logs/session_consistency/$LABEL.txt

echo logs/session_consistency/$LABEL.txt
grep "^1 " logs/session_consistency/$LABEL.txt | wc -l
cat        logs/session_consistency/$LABEL.txt | wc -l


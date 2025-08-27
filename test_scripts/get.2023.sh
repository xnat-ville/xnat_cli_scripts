#!/bin/bash

# These are get/export functions for all 2023 data
# This will be lists of subjects and sessions

LABEL=2023
SERVER=SHADOW08
AUTH=smoore

mkdir -p logs

echo "time ./scripts/list_subjects.sh $AUTH $SERVER test_data/projects.$LABEL.txt test_data/subjects.$LABEL.txt &> logs/list.subjects.$LABEL.log"
      time ./scripts/list_subjects.sh $AUTH $SERVER test_data/projects.$LABEL.txt test_data/subjects.$LABEL.txt &> logs/list.subjects.$LABEL.log

     ls -l test_data/subjects.$LABEL.txt
     wc -l test_data/subjects.$LABEL.txt

echo Subject list complete `date`; exit 0

#echo "time ./scripts/list_subjects_sessions.sh $AUTH $SERVER test_data/$LABEL.txt test_data/sessions.$LABEL.txt &> logs/list_sessions.$LABEL.log"
#      time ./scripts/list_subjects_sessions.sh $AUTH $SERVER test_data/$LABEL.txt test_data/sessions.$LABEL.txt &> logs/list_sessions.$LABEL.log
#
#     ls -l test_data/sessions.$LABEL.txt
#     wc -l test_data/sessions.$LABEL.txt
#


#echo "./scripts/get_session_xml.sh $AUTH $SERVER test_data/splits/sessions.$LABEL.txt  &> logs/get_sessions.$LABEL.log"
#time (./scripts/get_session_xml.sh $AUTH $SERVER test_data/splits/sessions.$LABEL.txt) &> logs/get_sessions.$LABEL.log

#echo "./scripts/processSessionXML.sh test_data/sessions.$LABEL.txt test_data/session_xml/ \
#	test_data/session_xml_processed test_data/inactive_projects_conditioned.txt  &> logs/process_sessions.$LABEL.log"
#time (./scripts/processSessionXML.sh test_data/sessions.$LABEL.txt test_data/session_xml/ \
#	test_data/session_xml_processed test_data/inactive_projects_conditioned.txt) &> logs/process_sessions.$LABEL.log



echo exit `date` ; exit 0







#if [[ -e test_data/splits/subjs.sessions.$LABEL ]] ; then
# echo  rm test_data/splits/subjs.sessions.$LABEL
#       rm test_data/splits/subjs.sessions.$LABEL
#fi
#
#echo mkdir -p test_data/splits
#     mkdir -p test_data/splits
#
#echo cp -p test_data/subjects_sessions.$LABEL.txt test_data/splits/subjs.sessions.$LABEL
#     cp -p test_data/subjects_sessions.$LABEL.txt test_data/splits/subjs.sessions.$LABEL
#
#echo ls -lt test_data/splits
#     ls -lt test_data/splits
#
#
#
#echo ./scripts/convert_subject_sessions.sh test_data/splits/subjs.sessions.$LABEL test_data/subjects.$LABEL.txt
#     ./scripts/convert_subject_sessions.sh test_data/splits/subjs.sessions.$LABEL test_data/subjects.$LABEL.txt

echo exit `date` ; exit 0

#echo "./scripts/find_orphan_session_folders.sh test_data/session_xml/subjs.sessions.00 > logs/session_consistency/$LABEL.txt"
#      ./scripts/find_orphan_session_folders.sh test_data/session_xml/subjs.sessions.00 > logs/session_consistency/$LABEL.txt
#
#echo logs/session_consistency/$LABEL.txt
#grep "^1 " logs/session_consistency/$LABEL.txt | wc -l
#cat        logs/session_consistency/$LABEL.txt | wc -l


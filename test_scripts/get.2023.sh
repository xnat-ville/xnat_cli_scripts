#!/bin/bash

# These are get/export functions for all 2023 data
# This will be lists of subjects and sessions

LABEL=2023
SERVER=LOCALHOST
AUTH=admin

mkdir -p logs

#echo "time ./scripts/list_subjects.sh $AUTH $SERVER test_data/projects.$LABEL.txt test_data/subjects.$LABEL.txt &> logs/list.subjects.$LABEL.log"
#      time ./scripts/list_subjects.sh $AUTH $SERVER test_data/projects.$LABEL.txt test_data/subjects.$LABEL.txt &> logs/list.subjects.$LABEL.log
#
#     ls -l test_data/subjects.$LABEL.txt
#     wc -l test_data/subjects.$LABEL.txt

echo "time ./scripts/list_subjects_sessions.sh $AUTH $SERVER test_data/subjects.$LABEL.txt test_data/sessions.$LABEL.txt &> logs/list_sessions.$LABEL.log"
      time ./scripts/list_subjects_sessions.sh $AUTH $SERVER test_data/subjects.$LABEL.txt test_data/sessions.$LABEL.txt &> logs/list_sessions.$LABEL.log

     ls -l test_data/sessions.$LABEL.txt
     wc -l test_data/sessions.$LABEL.txt



#echo "./scripts/get_session_xml.sh $AUTH $SERVER test_data/splits/sessions.$LABEL.txt  &> logs/get_sessions.$LABEL.log"
#time (./scripts/get_session_xml.sh $AUTH $SERVER test_data/splits/sessions.$LABEL.txt) &> logs/get_sessions.$LABEL.log

#echo "./scripts/processSessionXML.sh test_data/sessions.$LABEL.txt test_data/session_xml/ \
#	test_data/session_xml_processed test_data/inactive_projects_conditioned.txt  &> logs/process_sessions.$LABEL.log"
#time (./scripts/processSessionXML.sh test_data/sessions.$LABEL.txt test_data/session_xml/ \
#	test_data/session_xml_processed test_data/inactive_projects_conditioned.txt) &> logs/process_sessions.$LABEL.log



echo exit `date` ; exit 0


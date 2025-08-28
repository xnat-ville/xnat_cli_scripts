#!/bin/bash

LABEL=general
AUTH=admin
AUTH=admin
SERVER=LOCALHOST

mkdir -p logs

#echo "time ./scripts/create_investigators_from_json.sh $AUTH $SERVER  &> logs/create_investigators.$LABEL.txt"
#     (time ./scripts/create_investigators_from_json.sh $AUTH $SERVER) &> logs/create_investigators.$LABEL.txt

echo "time ./scripts/update_project_xml.sh $AUTH $SERVER  &> logs/project_xml.$LABEL.txt"
     (time ./scripts/update_project_xml.sh $AUTH $SERVER) &> logs/project_xml.$LABEL.txt

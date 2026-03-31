#!/bin/bash

 CONNECT="-d tip -h pg-tip-new -U tip"

 timestamp=`date +%Y%m%d.%H%M`

xnat_resource_rows() {
 SQL_SELECT="select
  r.format, r.uri
  from xnat_resource r "

 SQL_WHERE=" "

 SQL_TO="to ${1}"

 sql="\copy (${SQL_SELECT} ${SQL_WHERE} ) ${SQL_TO} "

 echo psql $CONNECT -c "$sql"
      psql $CONNECT -c "$sql"
}

xnat_resource_rows_verbose() {
 SQL_SELECT="select
  rm.status, rm.insert_date, rm.last_modified, r.format, r.uri
  from xnat_resource r, xnat_resource_meta_data rm "

 SQL_WHERE=" where r.resource_info = rm.meta_data_id "

 SQL_TO="to ${1}"

 sql="\copy (${SQL_SELECT} ${SQL_WHERE} ) ${SQL_TO} "

 echo psql $CONNECT -c "$sql"
      psql $CONNECT -c "$sql"
}

 set -e 
 mkdir -p data
 xnat_resource_rows_verbose data/xnat_resource.rows.verbose.txt
# date --date "7 days ago"

 wc -l data/xnat_resource.rows.verbose.txt

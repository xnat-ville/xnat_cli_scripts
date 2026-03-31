#!/bin/bash

# Data format
#active	2013-11-13 17:16:47.19	\N	DICOM	/data/tip/archive/RSN_GEN/arc001/dicom_upload/SCANS/11/DICOM/scan_11_catalog.xml
#active	2013-11-13 17:16:47.19	\N	DICOM	/data/tip/archive/RSN_GEN/arc001/dicom_upload/SCANS/19/DICOM/scan_19_catalog.xml

# Args:
#       Input datafile
#       ZFS/CEPH flag ('ZFS' or 'CEPH')
#       Output file
 detect_missing_scan_catalogs() {
  cut -f 5 ${1} > /tmp/raw_catalog.$$.txt
  if [[ ${2} == 'ZFS' ]] ; then
   mv /tmp/raw_catalog.$$.txt /tmp/catalog.$$.txt
  else
   sed -e 's-/data/-/ceph/-' /tmp/raw_catalog.$$.txt > /tmp/catalog.$$.txt
   rm -vf          /tmp/raw_catalog.$$.txt
  fi

  head  /tmp/catalog.$$.txt

  index=1
  max_rows=`cat /tmp/catalog.$$.txt | wc -l`
  rm -rf ${3}
  while read p ; do
    if [[ ! -e ${p} ]] ; then
      echo ${p} >> ${3}
      echo Missing ${p}
    fi
    if ! (( ${index} % 1000 )) ; then
      echo ${index} / ${max_rows}
    fi
    index=$(($index + 1))

  done < /tmp/catalog.$$.txt

  rm -f /tmp/catalog.$$.txt
 }


 timestamp=`date +%Y%m%d.%H%M`

 set -e
 mkdir -p data

#./storage_scripts/xnat_resource.sh

 detect_missing_scan_catalogs data/xnat_resource.rows.verbose.txt ZFS  data/missing_zfs_catalogs.txt
 detect_missing_scan_catalogs data/xnat_resource.rows.verbose.txt CEPH data/missing_ceph_catalogs.txt

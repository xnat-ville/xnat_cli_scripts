#!/bin/bash

# CNDA to CNDA2 Script Jenny Gurney, 6/5/2024

usage_and_exit() {
  echo "Arguments:
           Index file (tab delimited PROJECT_LABEL  SUBJECT_ID)
           Input directory (base folder)
           Output directory (base folder)
           Inactive project list
  "
    exit 1
}

check_args() {
  if [[ $# -ne 4 ]] ; then
    usage_and_exit
  fi
  if [ -z "${2}" ] || [ -z "${3}" ] || [ ! -d "${2}" ]; then
   usage_and_exit
  fi
}

# Compute path to XML file
# Returns that full path
# Arguments:
#             Base folder
#             Project Label
#             Subject ID
compute_xml_path() {
  full_path="${1}/${2}/${3}.xml"
  echo ${full_path}
}

# Check to see if the input file exists and exit if not found
# Arguments:
#             Path to expected file
exit_if_no_file() {
  if [[ ! -f ${1} ]] ; then
    echo "Expected file ${1} not found; processSubjectXML.sh will exit"
    exit 1
  fi
}

# Check to see if the input file contains the XNAT share keyword
# Arguments:
#             Path to input file
#contains_share_keyword() {
#  rtn="no"
#  grep "<xnat:share" ${1} > /dev/null
#  if [[ "$?" == "0" ]] ; then
#    rtn="yes"
#  fi
#
#  echo ${rtn}
#}

# Remove fixed fields from subject XML 
# We will overwrite the file contents, using a temporary file
# for intermediate work
# Arguments:
#            Path to XML
remove_fixed_fields() {
  local_tmp=/tmp/fixed_fields.$$.xml

  # Remove experiments from Subject XML 
  expStartLine=`cat $1 | grep -n '<xnat:experiments>'  | cut -d: -f1`
    expEndLine=`cat $1 | grep -n '</xnat:experiments>' | cut -d: -f1`

  if [ ! -z "$expStartLine" ] && [ ! -z "$expEndLine" ]; then
#   echo "sed  ${expStartLine},${expEndLine}d  $1 > $local_tmp"
          sed "${expStartLine},${expEndLine}d" $1 > $local_tmp
#   echo mv $local_tmp $1
         mv $local_tmp $1
  fi


  # Remove xnat:investigator from subject xml
  invStartLine=`cat $1 | grep -n '<xnat:investigator'   | cut -d: -f1`
    invEndLine=`cat $1 | grep -n '</xnat:investigator>' | cut -d: -f1`

  if [ ! -z "$invStartLine" ] && [ ! -z "$invEndLine" ]; then
#   echo "sed  ${invStartLine},${invEndLine}d  $1 > $local_tmp"
          sed "${invStartLine},${invEndLine}d" $1 > $local_tmp
    mv $local_tmp $1
  fi

  # Remove xnat:metadata from subject xml 
  metaStartLine=`cat $1 | grep -n '<xnat:metadata'   | cut -d: -f1`
    metaEndLine=`cat $1 | grep -n '</xnat:metadata>' | cut -d: -f1`

  if [ ! -z "$metaStartLine" ] && [ ! -z "$metaEndLine" ]; then
#   echo "sed  ${metaStartLine},${metaEndLine}d  $1 > $local_tmp"
          sed "${metaStartLine},${metaEndLine}d" $1 > $local_tmp
    mv $local_tmp $1
  fi

  if [[ -e $local_tmp ]] ; then
    echo "Local tmp file still exists $local_tmp; we will exit on that error"
    exit 1
  fi
}

# Remove hidden fields from subject XML 
# We will overwrite the file contents, using a temporary file
# for intermediate work
# Arguments:
#            Path to XML
remove_hidden_fields() {
  local_tmp=/tmp/hidden_fields.$$.xml
  sed 's/<!--hidden_fields[^>]*-->//g' ${1} > ${local_tmp}
  mv ${local_tmp} ${1}
}



# Remove projects that are no longer active from subject XML
# We will overwrite the file contents, using a temporary file
# for intermediate work
#            List of projects to remove
#            Path to XML
remove_inactive_shared_projects() {
  areShares=`cat $2 | grep -n "<xnat:share" | cut -d: -f1`
  if [ -z "${areShares}" ]; then
    # There are no shares to worry about
    return
  fi

  local_tmp=/tmp/shared.$$.xml

  # Grep using the entire index file to find any/all shared projects to remove
  # Reverse sort the line numbers in the next statement
  # We have to remove starting from the end of the file,
  # or else the line numbers will be off
  shares_removed="Shares removed: "
  delim=""
  for line in `cat $2 | grep -n -f $1 | cut -d: -f1 | sort -r -n`
  do
    p=`sed -n "$line,$line""p" $2`
    shares_removed="${shares_removed} ${delim}${p}"
    delim=","

#   echo "sed  ${line}d  $2 > $local_tmp"
          sed "${line}d" $2 > $local_tmp
#   echo mv $local_tmp $2
         mv $local_tmp $2
  done
  echo ${shares_removed}


# Remove xml share closure -- XNAT doesn't like it formatted this way and won't upload it
  # Reverse sort the line numbers in the next statement
  # We have to remove starting from the end of the file,
  # or else the line numbers will be off
  for line in `cat $2 | grep -n "</xnat:share>" | cut -d: -f1 | sort -r -n`
  do
#   echo "sed  ${line}d  $2 > $local_tmp"
          sed "${line}d" $2 > $local_tmp
#   echo mv $local_tmp $2
         mv $local_tmp $2
  done

# Add inline closure to any remaining shares
  for line in `cat $2 | grep -n "<xnat:share" | cut -d: -f1`
  do
#   echo "sed  ${line}s/>/\/>/  $2 > $local_tmp"
          sed "${line}s/>/\/>/" $2 > $local_tmp
#   echo mv $local_tmp $2
         mv $local_tmp $2
  done

# If there are no more shares in the XML, we need to remove "sharing"
  areShares=`cat $2 | grep -n "<xnat:share" | cut -d: -f1`
  if [ -z "${areShares}" ]; then
#   echo ""
#   echo Remove xnat:sharing
    # Reverse sort the line numbers in the next statement
    # We have to remove starting from the end of the file,
    # or else the line numbers will be off
    for line in `cat $2 | grep -n "xnat:sharing" | cut -d: -f1 | sort -r -n`
    do
#     echo "sed  ${line}d  $2 > $local_tmp"
            sed "${line}d" $2 > $local_tmp
#     echo mv $local_tmp $2
           mv $local_tmp $2
    done
  fi

  if [[ -e $local_tmp ]] ; then
    echo "Local tmp file still exists $local_tmp; we will exit on that error"
    exit 1
  fi
}

# Remove fixed fields from subject XML and shared project links for
# projects that are no longer active
# Arguments:
#            List of projects to remove
#            Path to input XML
#            Path to output XML
process_subject_xml () {
  echo "${2} ${3}"
  TMP=/tmp/$$.xml
  cp ${2} ${TMP}

  remove_fixed_fields  ${TMP}
  remove_hidden_fields ${TMP}
  remove_inactive_shared_projects ${1} ${TMP}

  output_folder=`dirname ${3}`
# echo mkdir -p ${output_folder}
       mkdir -p ${output_folder}

  echo mv ${TMP} ${3}
       mv ${TMP} ${3}
}

## Main starts here 
# Arguments:
#            Index file (tab delimited PROJECT_LABEL  SUBJECT_ID)
#            Input directory (base folder)
#            Output directory (base folder)
#            Inactive project list

set -e
check_args $*

echo Start $0 $* at `date`

INDEX_FILE=$1
INDIR=$2
OUTDIR=$3
REMOVESHARES=$4

#SED="sed -i bak"

# Perform a dry run to see if all input files exist
# Exit if anything is missing

missing_files=0
reviewed_files=0
while read -a project_subject ; do
  project=${project_subject[0]}
  subject=${project_subject[1]}

  input_xml_path=$( compute_xml_path  ${INDIR} ${project} ${subject} )
  if [[ ! -e ${input_xml_path} ]] ; then
    echo Missing: ${input_xml_path}
    missing_files=$(( $missing_files + 1 ))
  fi
  reviewed_files=$(( $reviewed_files + 1 ))
done < ${INDEX_FILE}

index_length=`cat ${INDEX_FILE} | wc -l`
echo "Dry run files reviewed: ${reviewed_files}"
echo "Index file length:      ${index_length}"
echo "Index file:             ${INDEX_FILE}"

if [[ $missing_files -ne 0 ]] ; then
  echo There are ${missing_files} files missing that are indexed in ${INDEX_FILE}
  echo This script will exit
  exit 1
fi

while read -a project_subject ; do
  project=${project_subject[0]}
  subject=${project_subject[1]}

# echo "$project / $subject"
   input_xml_path=$( compute_xml_path  ${INDIR} ${project} ${subject} )
  output_xml_path=$( compute_xml_path ${OUTDIR} ${project} ${subject} )
  if [[ -f ${output_xml_path} ]] ; then
    echo "Output XML already exists for $project / $subject"
    continue
  fi

  exit_if_no_file ${input_xml_path}
  process_subject_xml ${REMOVESHARES} ${input_xml_path} ${output_xml_path}
done < ${INDEX_FILE}


echo Complete $0 $* at `date`


##-for file in ${INDIR}/*.xml
##-do
##-   
##-   # Create copy of XML in outdir
##-   echo ""
##-   echo $file
##-   basename $file
##-   justFile=`basename $file` 
##-   newFile=${OUTDIR}/$justFile
##-   cp -f $file ${OUTDIR} 
##-
##-
##-   # Remove experiments from Subject XML 
##-   expStartLine=`cat $newFile | grep -n '<xnat:experiments>' | cut -d: -f1`
##-#  echo $expStartLine
##-   expEndLine=`cat $newFile | grep -n '</xnat:experiments>' | cut -d: -f1`
##-#  echo $expEndLine
##-   if [ ! -z "$expStartLine" ] && [ ! -z "$expEndLine" ]; then
##-#echo sed $newFile A
##-      echo "$SED '${expStartLine},${expEndLine}d' $newFile"
##-            $SED "${expStartLine},${expEndLine}d" $newFile   
##-   fi
##-




##-   while read shareProj
##-   do
##-#     echo $shareProj
##-      shareStartLine=`cat $newFile | grep -n project=\"${shareProj}\" | cut -d: -f1`
##-#     echo shareStartLine: $shareStartLine
##-      if [ ! -z "$shareStartLine" ]; then
##-#echo sed $newFile B
##-         echo "$SED \"${shareStartLine}d\" $newFile"
##-               $SED "${shareStartLine}d" $newFile
##-      fi
##-   done < ${REMOVESHARES}
##-
##-   # Remove hidden fields
##-   #echo "hidden fields"
##-   #let i=0
##-   #for line in `cat $newFile | grep -n "hidden_fields" | cut -d: -f1`
##-   #do
##-   #     #cat $newFile
##-   #     let changeLine=${line}-${i}
##-   #     echo ${line} "$changeLine"
##-   #     echo "sed -i \"${changeLine}d\" $newFile"
##-   #     sed -i "${changeLine}d" $newFile
##-   #     let i=$i+1
##-   #done
##-
##-   # Remove xml share closure -- XNAT doesn't like it formatted this way and won't upload it
##-   let i=0
##-   for line in `cat $newFile | grep -n "</xnat:share>" | cut -d: -f1`
##-   do
##-        let changeLine=${line}-${i}
##-#echo sed $newFile C
##-   	echo "$SED \"${changeLine}d\" $newFile"
##-              $SED  "${changeLine}d"  $newFile
##-        let i=$i+1
##-   done
##-
##-   # Add inline closure to any remaining shares
##-   for line in `cat $newFile | grep -n "<xnat:share" | cut -d: -f1`
##-   do
##-#echo sed $newFile D
##-      echo "$SED \"${line}s/>/\/>/\" $newFile"
##-            $SED  "${line}s/>/\/>/"  $newFile
##-   done
##-
##-   # If there are no more shares in the XML, we need to remove "sharing"
##-   areShares=`cat $newFile | grep -n "<xnat:share" | cut -d: -f1`
##-   if [ -z "${areShares}" ]; then
##-     let i=0
##-     for line in `cat $newFile | grep -n "xnat:sharing" | cut -d: -f1`
##-     do
##-        let changeLine=${line}-${i}
##-#echo sed $newFile E
##-        echo "$SED \"${changeLine}d\" $newFile"
##-              $SED  "${changeLine}d"  $newFile
##-        let i=$i+1
##-     done
##-   fi
##-
##-   # Remove xnat:investigator from subject xml
##-   invStartLine=`cat $newFile | grep -n '<xnat:investigator' | cut -d: -f1`
##-#  echo $invStartLine
##-   invEndLine=`cat $newFile | grep -n '</xnat:investigator>' | cut -d: -f1`
##-#  echo $invEndLine
##-   if [ ! -z "$invStartLine" ] && [ ! -z "$invEndLine" ]; then
##-#echo sed $newFile F
##-      echo "$SED '${invStartLine},${invEndLine}d' $newFile"
##-            $SED "${invStartLine},${invEndLine}d" $newFile
##-   fi
##-
##-   # Remove xnat:metadata from subject xml 
##-   metaStartLine=`cat $newFile | grep -n '<xnat:metadata' | cut -d: -f1`
##-#  echo $metaStartLine
##-   metaEndLine=`cat $newFile | grep -n '</xnat:metadata>' | cut -d: -f1`
##-#  echo $metaEndLine
##-   if [ ! -z "$metaStartLine" ] && [ ! -z "$metaEndLine" ]; then
##-#echo sed $newFile G
##-      echo "$SED '${metaStartLine},${metaEndLine}d' $newFile"
##-            $SED "${metaStartLine},${metaEndLine}d" $newFile
##-   fi
##-
##-   rm -f          "$newFile""bak"
##-   ls -l $newFile "$newFile""bak"
##-done 
##-

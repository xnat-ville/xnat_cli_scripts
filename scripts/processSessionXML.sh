#!/bin/bash

# CNDA to CNDA2 Migration Script Jenny Gurney, 6/6/2024

usage_and_exit() {
  echo "Arguments:
           Index file (tab delimited PROJECT_LABEL  SUBJECT_ID  SESSION_ID)
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
#             Session ID
compute_xml_path() {
  full_path="${1}/${2}/${4}.xml"
  echo ${full_path}
}

# Check to see if the input file exists and exit if not found
# Arguments:
#             Path to expected file
exit_if_no_file() {
  if [[ ! -f ${1} ]] ; then
    echo "Expected file ${1} not found; processSessionXML.sh will exit"
    exit 1
  fi
}

# Dry run to compare entries in index file to input files
# Arguments:
#             Index file (project / subject / session )
#             Input folder

dry_run() {
  my_index=$1
  my_folder=$2
  echo Begin dry run $my_index $my_folder `date`

  missing_files=0
  reviewed_files=0
  while read -a project_subject_session ; do
    project=${project_subject_session[0]}
    subject=${project_subject_session[1]}
    session=${project_subject_session[2]}

    input_xml_path=$( compute_xml_path  ${my_folder} ${project} ${subject} ${session} )
    if [[ ! -e ${input_xml_path} ]] ; then
      echo Missing: ${input_xml_path}
      missing_files=$(( $missing_files + 1 ))
    fi
    reviewed_files=$(( $reviewed_files + 1 ))
  done < ${my_index}

  index_length=`cat ${my_index} | wc -l`
  echo "Dry run files reviewed: ${reviewed_files}"
  echo "Index file length:      ${index_length}"
  echo "Index file:             ${my_index}"

  if [[ $missing_files -ne 0 ]] ; then
    echo There are ${missing_files} missing that are indexed in ${my_index}
    echo This script will exit `date`
    exit 1
  fi

  echo Complete dry run $my_index $my_folder `date`
}


# Remove broken shares
# We will overwrite the file contents, using a temporary file
# for intermediate work
# Arguments:
#            Path to XML
remove_broken_shares() {
  local_tmp=/tmp/broken_shares.$$.xml

  # Remove shares with no share project listed -- these are broken share links
  
  linesx=`cat $1 | grep -n "<xnat:share" | grep -v project | cut -d: -f1 | sort -r -n`

  for line in $linesx
  do
#   echo "sed ${line}d ${1} > ${local_tmp}"
          sed ${line}d ${1} > ${local_tmp}
#   echo "mv ${local_tmp} ${1}"
          mv ${local_tmp} ${1}
  done
}

# Remove projects that are no longer active from session XML
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
  lines=`cat $2 | grep -n -f $1 | cut -d: -f1 | sort -r -n`
# echo LINES: $lines
# echo $2
# echo $1
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
# echo ${shares_removed}

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
process_session_xml () {
# echo "${2} ${3}"
  TMP=/tmp/$$.xml
  cp ${2} ${TMP}

  remove_broken_shares ${TMP}
  remove_inactive_shared_projects ${1} ${TMP}

  output_folder=`dirname ${3}`
# echo mkdir -p ${output_folder}
       mkdir -p ${output_folder}
# echo mv ${TMP} ${3}
       mv ${TMP} ${3}
# ls -l ${2} ${3}
}


## Main starts here

set -e
check_args $*

echo Start $0 $* at `date`

INDEX_FILE=$1
BASE_INDIR=$2
BASE_OUTDIR=$3
REMOVESHARES=$4

#rm -rf   "${BASE_OUTDIR}"
mkdir -p "${BASE_OUTDIR}"

dry_run $INDEX_FILE $BASE_INDIR

while read -a project_subject_session ; do
  project=${project_subject_session[0]}
  subject=${project_subject_session[1]}
  session=${project_subject_session[2]}

# echo "$project / $subject / $session"
   input_xml_path=$( compute_xml_path  ${BASE_INDIR} ${project} ${subject} ${session} )
  output_xml_path=$( compute_xml_path ${BASE_OUTDIR} ${project} ${subject} ${session} )
  if [[ -f ${output_xml_path} ]] ; then
    echo "Output XML already exists for $project / $subject/ $session"
    continue
  fi

  exit_if_no_file ${input_xml_path}
  process_session_xml ${REMOVESHARES} ${input_xml_path} ${output_xml_path}
  echo "Output XML created for        $project / $subject/ $session"
done < ${INDEX_FILE}

echo Complete $0 $* at `date`
exit 1

##- for project_folder in $BASE_INDIR/* ; do
##-   echo $project_folder
##-   INDIR=$project_folder
##-   project_name=`basename $INDIR`
##-   OUTDIR=$BASE_OUTDIR/$project_name
##- 
##-   echo $INDIR
##-   echo $OUTDIR
##-   mkdir -p $OUTDIR
##- 
##-   for file in ${INDIR}/*.xml 
##-   do
##-      
##-      # Create copy of XML in outdir
##-      echo $file
##-      basename $file
##-      justFile=`basename $file` 
##-      newFile=${OUTDIR}/$justFile
##-      echo cp -f $file ${OUTDIR} 
##-           cp -f $file ${OUTDIR} 
##- 
##- 
##-   
##-      # Remove lines with strings found in remove list 
##-      #while read removeStr 
##-      #do
##-      #   echo ${removeStr}
##-      #   let i=0
##-      #   for line in `cat $newFile | grep -n "${removeStr}" | cut -d: -f1`
##-      #   do
##-      #      echo ${line}
##-      #      if [ ! -z "$line" ]; then
##-      #         let changeLine=${line}-${i}
##-      #         echo "sed -i \"${changeLine}d\" $newFile"
##-      #         sed -i "${changeLine}d" $newFile
##-      #         let i=$i+1
##-      #      fi
##-      #   done
##-      #done < ${REMOVELIST}
##-   
##-      # Remove shares with no share project listed -- these are broken share links
##-      let i=0
##-      for line in `cat $newFile | grep -n "<xnat:share" | grep -v project | cut -d: -f1`
##-      do
##-         let changeLine=${line}-${i}
##-   #      echo sed \"${changeLine}d\" $newFile
##-              sed  "${changeLine}d"  $newFile > /tmp/sed.$$.txt
##-   #      echo mv /tmp/sed.$$.txt $newFile
##-              mv /tmp/sed.$$.txt $newFile
##-         let i=$i+1
##-      done
##-   
##-      while read shareProj
##-      do
##-         shareStartLine=`cat $newFile | grep -n project=\"${shareProj}\" | cut -d: -f1`
##-         if [ ! -z "$shareStartLine" ]; then
##-   #         echo sed \"${shareStartLine}d\" $newFile
##-                 sed "${shareStartLine}d" $newFile > /tmp/sed.$$.txt
##-   #         echo mv /tmp/sed.$$.txt $newFile
##-                 mv /tmp/sed.$$.txt $newFile
##-         fi
##-      done < ${REMOVESHARES}
##-   
##-      # Remove xml share closure -- XNAT doesn't like it formatted this way and won't upload it
##-      let i=0
##-      for line in `cat $newFile | grep -n "</xnat:share>" | cut -d: -f1`
##-      do
##-           let changeLine=${line}-${i}
##-   #        echo sed \"${changeLine}d\" $newFile
##-                sed  "${changeLine}d"  $newFile > /tmp/sed.$$.txt
##-   #        echo mv /tmp/sed.$$.txt $newFile
##-                mv /tmp/sed.$$.txt $newFile
##-           let i=$i+1
##-      done
##-   
##-      # Add inline closure to any remaining shares
##-      for line in `cat $newFile | grep -n "<xnat:share" | cut -d: -f1`
##-      do
##-   #      echo "sed \"${line}s/>/\/>/\" $newFile"
##-              sed "${line}s/>/\/>/" $newFile > /tmp/sed.$$.txt
##-         mv /tmp/sed.$$.txt $newFile
##-      done   
##-   
##-      # If there are no more shares in the XML, we need to remove "sharing"
##-      areShares=`cat $newFile | grep -n "<xnat:share" | cut -d: -f1`
##-      if [ -z "${areShares}" ]; then
##-        let i=0 
##-        for line in `cat $newFile | grep -n "xnat:sharing" | cut -d: -f1`
##-        do
##-           let changeLine=${line}-${i}
##-           echo "sed \"${changeLine}d\" $newFile"
##-                 sed  "${changeLine}d" $newFile > /tmp/sed.$$.txt
##-           mv /tmp/sed.$$.txt $newFile
##-           let i=$i+1
##-        done
##-      fi
##-   
##-      # Find/replace strings from replace list 
##-      #while read findReplaceStr
##-      #do
##-      #findStr=`echo $findReplaceStr | cut -d',' -f1`
##-      #replaceStr=`echo $findReplaceStr | cut -d',' -f2`
##-      #echo "find\/replace $findStr $replaceStr"
##-      #if [ ! -z "${findStr}" ]; then
##-      #   for line in `cat $newFile | grep -n "${findStr}" | cut -d: -f1`
##-      #   do
##-      #      echo "sed -i \"${line}s/${findStr}/${replaceStr}/g\" $newFile"
##-      #      sed -i "${line}s/${findStr}/${replaceStr}/g" $newFile
##-      #   done
##-      #fi
##-      #done < ${REPLACELIST}   
##-    
##-   done 
##- done

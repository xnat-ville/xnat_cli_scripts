#!/bin/bash

# CNDA to CNDA2 Migration Script Jenny Gurney, 5/23/2024

# Remove single alias
# Arguments:
#            Input/output file
#            Alias to remove
remove_single_alias() {
  TMPFILE=/tmp/alias.$$.txt
  pattern="^$2</xnat:alias>"
  grep -n -e "$pattern" $1 &> $TMPFILE
  if [[ $? -eq 0 ]] ; then
    echo $1
    line_number=`sed -e 's/:.*$//' $TMPFILE`
    line_number=$(( $line_number - 1 ))
    sed "${line_number}d" $1 | grep -v -e "$pattern" > $TMPFILE
    mv $TMPFILE $1
  else
    rm -f $TMPFILE
  fi
}


# Remove duplicate aliases
# Arguments:
#            Input/output file
remove_duplicate_aliases() {
 remove_single_alias $1 COGED
 remove_single_alias $1 facs
 remove_single_alias $1 HYPO
 remove_single_alias $1 Hy5
 remove_single_alias $1 hy5
}

# Remove publications
# Arguments:
#            Input/output file
remove_publications() {
 TMPFILE=/tmp/publications.$$.txt
 sed		\
	-e 's/^<xnat:publications>/<!--<xnat:publications>/' \
	-e 's_^</xnat:publications>$_</xnat:publications>-->_' \
   $1 > $TMPFILE
 mv $TMPFILE $1
}

## Main starts here

INDIR=$1
OUTDIR=$2

REMOVEPROJ=$3
REMOVEDATA=$4

echo Start $0 $* `date`

mkdir -p $OUTDIR

file $INDIR
file $OUTDIR

if [ -z "${INDIR}" ] || [ -z "${OUTDIR}" ] || [ ! -d "${INDIR}" ] || [ ! -d "${OUTDIR}" ]; then
   echo "Usage: processProjectXML.sh InDirectory OutDirectory RemoveShareProjsList RemoveDataTypesList"
   exit 1
fi
if [[ ! -f ${REMOVEDATA} ]]; then
   echo Datatypes to remove not found: ${REMOVEDATA}
   exit 1
fi

for file in ${INDIR}/*.xml
do
   
   # Create copy of XML in outdir
   echo $file
   basename $file
   justFile=`basename $file` 
   newFile=${OUTDIR}/$justFile
   cp -f $file ${OUTDIR} 

   # Remove all hidden fields
   sed -ibak 's/<!--hidden_fields[^>]*-->//g' ${newFile}

   # Remove StudyProtocols for removed data types
   projId=`echo $justFile | cut -d. -f1`
   while read unusedData
   do 
#     echo "protStartLine= cat $newFile | grep -n '<xnat:studyProtocol ID=\"${projId}_${unusedData}\"' | cut -d: -f1"
            protStartLine=`cat $newFile | grep -n "<xnat:studyProtocol ID=\"${projId}_${unusedData}\"" | cut -d: -f1`
#     echo Protocol Start Line: $protStartLine
      if [ ! -z ${protStartLine} ]; then
         nextProtClose=`tail -n +${protStartLine} $newFile | grep -n '</xnat:studyProtocol>' | head -1 | cut -d: -f1`
         let protEndLine=${protStartLine}+${nextProtClose}-1
#        echo $protEndLine
         if [ ! -z "$protStartLine" ] && [ ! -z "$protEndLine" ]; then
            if [ ${protEndLine} -gt ${protStartLine} ]; then
#              echo "sed -ibak  ${protStartLine},${protEndLine}d  $newFile"
                     sed -ibak "${protStartLine},${protEndLine}d" $newFile 
            else
               echo "Skipped, protocol end line ${protEndLine} is not larger than protocol start line ${protStartLine}"
            fi  
         fi
      fi 
   done < ${REMOVEDATA}

   # Remove empty lines
#  echo  sed -ibak '/^$/d' ${newFile}
         sed -ibak '/^$/d' ${newFile}
#  echo  rm -f ${newFile}bak
         rm -f ${newFile}bak
   remove_duplicate_aliases ${newFile}
   remove_publications      ${newFile}

done 

echo Complete $0 $* `date`

#!/bin/bash

# CNDA to CNDA2 Migration Script Jenny Gurney, 5/23/2024

INDIR=$1
OUTDIR=$2

REMOVEPROJ=$3
REMOVEDATA=$4

mkdir -p $OUTDIR

file $INDIR
file $OUTDIR

if [ -z "${INDIR}" ] || [ -z "${OUTDIR}" ] || [ ! -d "${INDIR}" ] || [ ! -d "${OUTDIR}" ]; then
   echo "Usage: processProjectXML.sh InDirectory OutDirectory RemoveShareProjsList RemoveDataTypesList"
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
   sed -i bak 's/<!--hidden_fields[^>]*-->//g' ${newFile}

   # Remove StudyProtocols for removed data types
   projId=`echo $justFile | cut -d. -f1`
   while read unusedData
   do 
      echo "protStartLine= cat $newFile | grep -n '<xnat:studyProtocol ID=\"${projId}_${unusedData}\"' | cut -d: -f1"
            protStartLine=`cat $newFile | grep -n "<xnat:studyProtocol ID=\"${projId}_${unusedData}\"" | cut -d: -f1`
      echo Protocol Start Line: $protStartLine
      if [ ! -z ${protStartLine} ]; then
         nextProtClose=`tail -n +${protStartLine} $newFile | grep -n '</xnat:studyProtocol>' | head -1 | cut -d: -f1`
         let protEndLine=${protStartLine}+${nextProtClose}-1
         echo $protEndLine
         if [ ! -z "$protStartLine" ] && [ ! -z "$protEndLine" ]; then
            if [ ${protEndLine} -gt ${protStartLine} ]; then
               echo "sed -i bak '${protStartLine},${protEndLine}d' $newFile"
                     sed -i bak "${protStartLine},${protEndLine}d" $newFile 
            else
               echo "Skipped, protocol end line ${protEndLine} is not larger than protocol start line ${protStartLine}"
            fi  
         fi
      fi 
   done < ${REMOVEDATA}

   # Remove empty lines
   echo  sed -i bak '/^$/d' ${newFile}
         sed -i bak '/^$/d' ${newFile}
   echo  rm -f ${newFile}bak
         rm -f ${newFile}bak

done 

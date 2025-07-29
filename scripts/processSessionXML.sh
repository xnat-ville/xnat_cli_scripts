#!/bin/bash

# CNDA to CNDA2 Migration Script Jenny Gurney, 6/6/2024


BASE_INDIR=$1
BASE_OUTDIR=$2
REMOVESHARES=$3

rm -rf   "${BASE_OUTDIR}"
mkdir -p "${BASE_OUTDIR}"

if [ -z "${BASE_INDIR}" ] || [ -z "${BASE_OUTDIR}" ] || [ ! -d "${BASE_INDIR}" ] || [ ! -d "${BASE_OUTDIR}" ]; then
   echo "Usage: processSessionXML.sh InDirectory OutDirectory ListOfProjectSharesToBeRemoved"
   exit 1
fi

for project_folder in $BASE_INDIR/* ; do
  echo $project_folder
  INDIR=$project_folder
  project_name=`basename $INDIR`
  OUTDIR=$BASE_OUTDIR/$project_name

  echo $INDIR
  echo $OUTDIR
  mkdir -p $OUTDIR

  for file in ${INDIR}/*.xml 
  do
     
     # Create copy of XML in outdir
     echo $file
     basename $file
     justFile=`basename $file` 
     newFile=${OUTDIR}/$justFile
     echo cp -f $file ${OUTDIR} 
          cp -f $file ${OUTDIR} 


  
     # Remove lines with strings found in remove list 
     #while read removeStr 
     #do
     #   echo ${removeStr}
     #   let i=0
     #   for line in `cat $newFile | grep -n "${removeStr}" | cut -d: -f1`
     #   do
     #      echo ${line}
     #      if [ ! -z "$line" ]; then
     #         let changeLine=${line}-${i}
     #         echo "sed -i \"${changeLine}d\" $newFile"
     #         sed -i "${changeLine}d" $newFile
     #         let i=$i+1
     #      fi
     #   done
     #done < ${REMOVELIST}
  
     # Remove shares with no share project listed -- these are broken share links
     let i=0
     for line in `cat $newFile | grep -n "<xnat:share" | grep -v project | cut -d: -f1`
     do
        let changeLine=${line}-${i}
  #      echo sed \"${changeLine}d\" $newFile
             sed  "${changeLine}d"  $newFile > /tmp/sed.$$.txt
  #      echo mv /tmp/sed.$$.txt $newFile
             mv /tmp/sed.$$.txt $newFile
        let i=$i+1
     done
  
     while read shareProj
     do
        shareStartLine=`cat $newFile | grep -n project=\"${shareProj}\" | cut -d: -f1`
        if [ ! -z "$shareStartLine" ]; then
  #         echo sed \"${shareStartLine}d\" $newFile
                sed "${shareStartLine}d" $newFile > /tmp/sed.$$.txt
  #         echo mv /tmp/sed.$$.txt $newFile
                mv /tmp/sed.$$.txt $newFile
        fi
     done < ${REMOVESHARES}
  
     # Remove xml share closure -- XNAT doesn't like it formatted this way and won't upload it
     let i=0
     for line in `cat $newFile | grep -n "</xnat:share>" | cut -d: -f1`
     do
          let changeLine=${line}-${i}
  #        echo sed \"${changeLine}d\" $newFile
               sed  "${changeLine}d"  $newFile > /tmp/sed.$$.txt
  #        echo mv /tmp/sed.$$.txt $newFile
               mv /tmp/sed.$$.txt $newFile
          let i=$i+1
     done
  
     # Add inline closure to any remaining shares
     for line in `cat $newFile | grep -n "<xnat:share" | cut -d: -f1`
     do
  #      echo "sed \"${line}s/>/\/>/\" $newFile"
             sed "${line}s/>/\/>/" $newFile > /tmp/sed.$$.txt
        mv /tmp/sed.$$.txt $newFile
     done   
  
     # If there are no more shares in the XML, we need to remove "sharing"
     areShares=`cat $newFile | grep -n "<xnat:share" | cut -d: -f1`
     if [ -z "${areShares}" ]; then
       let i=0 
       for line in `cat $newFile | grep -n "xnat:sharing" | cut -d: -f1`
       do
          let changeLine=${line}-${i}
          echo "sed \"${changeLine}d\" $newFile"
                sed  "${changeLine}d" $newFile > /tmp/sed.$$.txt
          mv /tmp/sed.$$.txt $newFile
          let i=$i+1
       done
     fi
  
     # Find/replace strings from replace list 
     #while read findReplaceStr
     #do
     #findStr=`echo $findReplaceStr | cut -d',' -f1`
     #replaceStr=`echo $findReplaceStr | cut -d',' -f2`
     #echo "find\/replace $findStr $replaceStr"
     #if [ ! -z "${findStr}" ]; then
     #   for line in `cat $newFile | grep -n "${findStr}" | cut -d: -f1`
     #   do
     #      echo "sed -i \"${line}s/${findStr}/${replaceStr}/g\" $newFile"
     #      sed -i "${line}s/${findStr}/${replaceStr}/g" $newFile
     #   done
     #fi
     #done < ${REPLACELIST}   
   
  done 
done

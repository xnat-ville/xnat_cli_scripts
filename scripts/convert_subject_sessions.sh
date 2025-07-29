#!/bin/bash

# Main starts here
# Arguments
#              Input file of subjects/sessions (long file)
#              Output file of subjects


if [ $# -ne 2 ]; then
    echo "Arguments: input_subjects_sessions output_subjects_only"
    exit 1
fi

subjects_sessions="$1"
subjects="$2"

TEMP=/tmp/$$.subj.txt
rm -f ${TEMP}
TAB="	"
while read -r -a sub_sess ; do
  echo "${sub_sess[0]}${TAB}${sub_sess[1]}" >> ${TEMP}
done < $subjects_sessions

sort ${TEMP} | uniq > ${subjects}
wc -l ${subjects_sessions} ${TEMP} ${subjects}

rm -f ${TEMP}

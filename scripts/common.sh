#!/bin/bash

# Common functions for CLI scripts

# Returns the URL of the XNAT that is the target of a function.
# Maps input key to a value
# EXISTING
# PRODUCTION-COPY
# PRODUCTION-LIVE
# DEV-COPY
# DEV-LIVE
# LOCALHOST
# TARGET

get_xnat_url() {
 url=""

 case "$1" in
  # Todo: Need to fix
  "TARGET")
   url="http://localhost:8080" ;;

  "EXISTING")
   url="https://cnda-shadow07.nrg.wustl.edu";;

  # Todo: Need to fix this (cnda-gold.wustl.edu)
  "PRODUCTION-COPY")
   url="https://cnda-dev-archive1.nrg.wustl.edu";;

  # Todo: Need to fix this (cnda.wustl.edu)
  "PRODUCTION-LIVE")
   url="https://cnda-dev-archive1.nrg.wustl.edu";;

  "DEV-COPY")
   url="https://cnda-dev-archive1.nrg.wustl.edu";;

  "DEV-LIVE")
   url="https://cnda-dev-archive1.nrg.wustl.edu";;

  "LOCALHOST")
   url="http://localhost:8080" ;;

  *)
   >&2 echo "get_xnat_url does not recognize input key: $1"
   >&2 echo "Should be one of: EXISTING, PRODUCTION-COPY, PRODUCTION-LIVE, DEV-COPY, DEV-LIVE, LOCALHOST"
   return 1 ;;
 esac

 echo "$url"
}

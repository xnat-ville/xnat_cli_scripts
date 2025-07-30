#!/bin/python3
"""
connect_test.py
--------------------------------------------------------------------------------
Test connection using xnatpy. For example:
  python3 connect.py -a smoore -x https://cnda.wustl.edu 

"""

import argparse
import xnat.mixin
from xnat.session import XNATSession

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List projects from an XNAT system")
    parser.add_argument('-x', '--xnat',            dest='url',                      help="URL to XNAT, default is http://localhost:8080")
    parser.add_argument('-a', '--auth',            dest='auth',                     help="User authentication/login for access to XNAT", required=True)
    parser.add_argument('-p', '--password',        dest='password',                 help="Password for XNAT authentication", required=False)

    args = parser.parse_args()

    args.url = "localhost:8080" if args.url is None else args.url

    xnat_extensions = False

    session = xnat.connect(args.url, user=args.auth, password=args.password, extension_types=xnat_extensions)

    session.disconnect()  # Ensures cleanup even if an error occurs


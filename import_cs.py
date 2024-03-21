# program that combines functionality of calling companies and contacts (the "c's") api:
# 
#  1. api call to create companies
#  2. api call to create contacts

# program is called from command line as such:
#   % python3 import_cs.py <contacts file name>
# note: contacts file should be contained in same folder as program

import sys
import time
from companies_api import callCompaniesAPI
from contacts_api import callContactsAPI
from contacts_api import getContacts

def main():
    print("\nStarting program...\n")

    # get contacts file from command line
    if len(sys.argv) < 2:   # ensure enough arguments are passed
        print(sys.argv)
        raise AssertionError("Not enough arguments specified")

    contactsFilename = sys.argv[1]

    # api call to create companies
    print("Starting companies API call...\n")
    callCompaniesAPI(contactsFilename)

    # wait between api calls so that when contacts are created, ensure their companies already exist in the db
    print("Waiting 10 seconds for companies to populate database before importing contacts...\n")
    for i in range(10, 0, -1):
        print(i)
        time.sleep(1)

    # api call to create contacts
    print("Starting contacts API call...\n")
    callContactsAPI(contactsFilename)


if __name__ == "__main__":
    main()
# program that combines functionality of calling companies and contacts (the "c's") api:
# 
#  1. api call to create companies
#  2. api call to create contacts

# program is called from command line as such:
#   % python3 import_cs.py <contacts file name/path>

import sys
from companies_api import callCompaniesAPI
from contacts_api import callContactsAPI

def main():
    # get contacts and emails files from command line
    if len(sys.argv) < 3:   # ensure enough arguments are passed
        raise AssertionError("Not enough arguments specified")

    contactsFilepath = sys.argv[2]

    # api call to create companies
    callCompaniesAPI(contactsFilepath)

    # api call to create contacts
    callContactsAPI(contactsFilepath)


if __name__ == "__main__":
    main()
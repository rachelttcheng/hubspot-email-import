# program that combines functionality of calling companies and contacts (the "c's") api:
# 
#  1. api call to create companies
#  2. api call to create contacts

# program is called from command line as such:
#   % python3 import_cs.py <contacts file name>
# note: contacts file should be contained in same folder as program

import sys
import hubspot
import time
from companies_api import HubSpotCompaniesAPI
from contacts_api import HubSpotContactsAPI
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
CLIENT = hubspot.Client.create(access_token=ACCESS_TOKEN)

def main():
    print("\nStarting program...\n")

    # get contacts file from command line
    if len(sys.argv) < 2:   # ensure enough arguments are passed
        print(sys.argv)
        raise AssertionError("Not enough arguments specified")

    contactsFilename = sys.argv[1]

    # api call to create companies
    print("Starting companies API call...\n")
    CompaniesAPI = HubSpotCompaniesAPI(ACCESS_TOKEN, CLIENT)
    CompaniesAPI.import_companies_file(contactsFilename)

    # wait between api calls so that when contacts are created, ensure their companies already exist in the db
    print("Waiting 10 seconds for companies to populate database before importing contacts...\n")
    for i in range(10, 0, -1):
        print(i)
        time.sleep(1)

    # re-populate existing companies in db, with updated db info
    CompaniesAPI.get_existing_companies()

    # api call to create contacts
    print("Starting contacts API call...\n")
    ContactsAPI = HubSpotContactsAPI(ACCESS_TOKEN, CLIENT)
    ContactsAPI.import_contacts_file(contactsFilename, CompaniesAPI.existing_db_companies)


if __name__ == "__main__":
    main()
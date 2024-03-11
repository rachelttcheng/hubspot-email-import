# create/update companies before contacts
# url = 'https://api.hubapi.com/crm/v3/objects/companies/batch/create'

# run on command line as such:
# % python3 companies-api.py <contacts filename/path>
# e.g.
# % python3 companies-api.py ./data/sample-contacts.csv

import hubspot
import sys
import csv
import requests
import json
from ratelimiter import checkLimit
from pprint import pprint
from hubspot.crm.companies import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
COMPANY_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/companies/search"

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

# given company domain, checks if it already exists within database to prevent duplicates
def companyExists(companyDomain):
    # insert company domain into query and create relevant headers
    payload = json.dumps({"query": companyDomain})
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN
    }

    # make request and get response data, with rate limiting
    checkLimit()
    response = requests.request("POST", COMPANY_SEARCH_URL, headers=headers, data=payload)
    responseData = response.json()

    # check "total" matches
    if responseData["total"] == 0:
        return False
    else:
        return True

def main():
    # ensure input file specified on command line
    if len(sys.argv) < 2:
        raise AssertionError("No contact file specified")
    
    contactsFileName = sys.argv[2]

    # flow company info into json format
    companies = []
    with open(contactsFileName, newline='') as contactsFile:
        companies = [
            {
                "properties": {
                    "domain": row["company domain"]
                }
            }
            for row in csv.DictReader(contactsFile) if not companyExists(row["company domain"])
        ]

    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies)

    try:
        api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

if __name__ == "__main__":
    main()
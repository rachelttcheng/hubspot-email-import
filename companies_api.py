# create/update companies before contacts, in batches of 100 (size limit)
# url = 'https://api.hubapi.com/crm/v3/objects/companies/batch/create'

# run on command line as such:
# % python3 companies-api.py <contacts filename/path>
# e.g.
# % python3 companies-api.py ./data/sample-contacts.csv

import hubspot
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

def callCompaniesAPI(contactsFilename):
    # flow company info into json format
    with open(contactsFilename, newline='') as contactsFile:
        # variables to keep track of batches
        companies = set()
        current_batch_size = 0
        companies_batch = list()

        # iterate through csv file and add companies that don't already exist, either within local companies list or hubspot databse into batch request
        for row in csv.DictReader(contactsFile):
            # check if company already exists within larger file set, then check if it already exists within hubspot database
            if row["company domain"] not in companies and not companyExists(row["company domain"]):
                companies.add(row["company domain"])
                companies_batch.append({"properties": {"domain": row["company domain"]}})
                current_batch_size += 1

                # push batch if size is at limit of 100
                if current_batch_size == 100:
                    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies_batch)

                    try:
                        api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                        pprint(api_response)
                        print("\nCompany batch pushed successfully.\n")
                    except ApiException as e:
                        print("Exception when calling batch_api->create: %s\n" % e)

                    # reset batch
                    current_batch_size = 0
                    companies_batch = list()

        # make sure to push leftover/last batch if it didn't hit batch limit of 100
        if current_batch_size > 0:
            batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies_batch)

            try:
                api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                pprint(api_response)
                print("\nCompany batch pushed successfully.\n")
            except ApiException as e:
                print("Exception when calling batch_api->create: %s\n" % e)
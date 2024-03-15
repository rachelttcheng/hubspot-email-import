# import contacts (after companies)
# all contacts need to be in JSON format, associated to company object

# run on command line as such:
# % python3 contacts-api.py <contacts filename/path>
# e.g.
# % python3 email-api.py ./data/sample-contacts.csv

import hubspot
import csv
import requests
import json
from ratelimiter import checkLimit
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
COMPANY_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/companies/search"
CONTACTS_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

# given a company domain (unique identifier), makes request to hubspot api and returns object id within hubspot database
def getAssociatedCompanyID(companyDomain):
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

    print(responseData)

    # handle if no result; still TO DO in regards to if program should terminate or not
    if responseData["total"] == 0:
        print(f"Company {companyDomain} does not exist, cannot associate to contact\n")

    # return company id
    return responseData["results"][0]["id"]

# given a contact email, makes request to hubspot api and ensures no duplication of existing contact (prevent conflict erros)
def contactAlreadyExists(contactEmail):
    # insert company domain into query and create relevant headers
    payload = json.dumps({"query": contactEmail})
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN
    }

    # make request and get response data, with rate limiting
    checkLimit()
    response = requests.request("POST", CONTACTS_SEARCH_URL, headers=headers, data=payload)
    responseData = response.json()

    # check if any matches exist and return accordingly
    if responseData["total"] == 0:
        return False
    else:
        return True

def callContactsAPI(contactsFilename):
    # flow csv data into nested json format
    contacts = []
    with open(contactsFilename, newline='') as contactsFile:
        contacts = [
            {
                "associations": [{
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 1
                    }],
                    "to": {
                        "id": getAssociatedCompanyID(row["company domain"])
                    }
                }],
                "properties": {
                    "email": row["email"],
                    "firstname": row["first name"],
                    "lastname": row["last name"],
                    "company": row["company"],
                    "website": row["company domain"]
                }
            }
            for row in csv.DictReader(contactsFile) if not contactAlreadyExists(row["email"])
        ]

    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts)

    try:
        api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)
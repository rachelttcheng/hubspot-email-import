# import contacts (after companies)
# all contacts need to be in JSON format, associated to company object

# url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/create'

import hubspot
import csv
import requests
import json
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException

client = hubspot.Client.create(access_token="YOUR_ACCESS_TOKEN")

COMPANY_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/companies/search"

def getAssociatedCompanyID(companyDomain):
    # insert company domain into query and create relevant headers
    payload = json.dumps({
        "query": companyDomain
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
    }

    # make request and return comapny id from response
    response = requests.request("POST", COMPANY_SEARCH_URL, headers=headers, data=payload)

    # handle if no result; still TO DO in regards to if program should terminate or not
    if not response["total"]:
        print("Associated company does not exist\n")

    return response["results"][0]["id"]

contacts = []

with open("CONTACTS_FILE.csv", newline='') as contactsFile:
    contacts = [
        {
            "associations": [{
                "types": [{
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": 1
                }],
                "to": {
                    "id": getAssociatedCompanyID(row["company domain"])  # should be id of company TO DO
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
        for row in csv.DictReader(contactsFile)
    ]

batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts)

try:
    api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling batch_api->create: %s\n" % e)
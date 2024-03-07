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

# given a company domain (unique identifier), makes request to hubspot api and returns object id within hubspot databse
def getAssociatedCompanyID(companyDomain):
    # insert company domain into query and create relevant headers
    payload = json.dumps({
        "query": companyDomain
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
    }

    # make request
    response = requests.request("POST", COMPANY_SEARCH_URL, headers=headers, data=payload)

    # handle if no result; still TO DO in regards to if program should terminate or not
    if not response["total"]:
        print(f"Company {companyDomain} does not exist, cannot associate to contact\n")

    # return company id
    return response["results"][0]["id"]

def main():
    # flow csv data into nested json format
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
            for row in csv.DictReader(contactsFile)
        ]

    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts)

    try:
        api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

if __name__ == "__main__":
    main()
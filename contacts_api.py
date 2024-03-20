# import contacts (after companies), limited to batch sizes of 100
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

    # handle if no result; still TO DO in regards to if program should terminate or not
    if responseData["total"] == 0:
        print(f"Company {companyDomain} does not exist, cannot associate to contact\n")

    # return company id
    return responseData["results"][0]["id"]

# given a contact email, makes request to hubspot api and ensures no duplication of existing contact (prevent conflict errors)
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
    with open(contactsFilename, newline='') as contactsFile:
        # variables to keep track of locally seen contacts, and current batch
        contacts = set()
        contacts_batch = list()
        total_contacts_pushed = 0

        # iterate through contacts file and add unique contacts to batch request
        for row in csv.DictReader(contactsFile):
            # check if contact already exists within larger file set, then check if it already exists within hubspot database
            if row["email"] not in contacts and not contactAlreadyExists(row["email"]):
                contacts.add(row["email"])
                contacts_batch.append({
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
                })
            
                # push batch if at batch size limit of 100
                if len(contacts_batch) == 100:
                    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts_batch)

                    try:
                        api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                        total_contacts_pushed += len(api_response.results)
                        # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
                        print("\nContacts batch pushed successfully.\n")
                    except ApiException as e:
                        print("Exception when calling batch_api->create: %s\n" % e)

                    # reset batch
                    contacts_batch = list()
        
        # make sure to push leftover/last batch if it didn't hit batch limit of 100
        if len(contacts_batch) > 0:
            batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts_batch)

            try:
                api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                total_contacts_pushed += len(api_response.results)
                # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
                print("\nContacts batch pushed successfully.\n")
            except ApiException as e:
                print("Exception when calling batch_api->create: %s\n" % e)

        print(f"\n{total_contacts_pushed} contacts pushed successfully.\n")
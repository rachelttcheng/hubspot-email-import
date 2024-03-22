# import contacts (after companies), limited to batch sizes of 100
# all contacts need to be in JSON format, associated to company object

import hubspot
import csv
import requests
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken
from companies_api import getCompanies

ACCESS_TOKEN = fetchToken()
CONTACTS_GET_URL = "https://api.hubapi.com/crm/v3/objects/contacts"
EXISTING_CONTACTS_IN_DB = dict()
COMPANIES_IN_DB = dict()

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

# request database for info on all existing contacts
def getContacts():
    params =  {"properties": ["email"]}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN
    }

    # make request for all existing contacts in db and filter results to get set with all contact emails
    response = requests.get(CONTACTS_GET_URL, headers=headers, params=params)
    responseData = response.json()
    all_results = {contact['properties']['email']: contact['id'] for contact in responseData['results']}

    # account for result pagination, get all results
    while ("paging" in responseData):
        response = requests.get(responseData['paging']['next']['link'], headers=headers, params=params)
        responseData = response.json()
        all_results.update({contact['properties']['email']: contact['id'] for contact in responseData['results']})
    
    return all_results

# given a company domain (unique identifier) returns object id within hubspot database
def getAssociatedCompanyID(companyDomain):
    if companyDomain not in COMPANIES_IN_DB.keys():
        print(f"Company {companyDomain} does not exist, cannot associate to contact\n")
    
    return COMPANIES_IN_DB[companyDomain]

# given a contact email, check if it exists in db already to ensure no duplication of existing contact (prevent conflict errors)
def contactAlreadyExists(contactEmail):
    # be sure to account for case sensitivity
    if contactEmail.lower() in EXISTING_CONTACTS_IN_DB.keys():
        return True
    else:
        return False

def callContactsAPI(contactsFilename):
    # get all existing contacts from database and flow into global variable
    print("Retrieving all existing contacts from database...\n")
    global EXISTING_CONTACTS_IN_DB
    EXISTING_CONTACTS_IN_DB = getContacts()

    # get all companies within database, including their id; should include newly created companies
    print("Retrieving all companies and their IDs from database...\n")
    global COMPANIES_IN_DB
    COMPANIES_IN_DB = getCompanies()

    # flow csv data into nested json format
    print("Flowing in potential new contacts...\n")
    with open(contactsFilename, newline='') as contactsFile:
        # variables to keep track of locally seen contacts, and current batch
        requested_contacts = set()
        contacts_batch = list()
        total_contacts_pushed = 0

        # iterate through contacts file and add unique contacts to batch request
        for row in csv.DictReader(contactsFile):
            # check if contact already exists within larger file set, then check if it already exists within hubspot database
            if row["email"] not in requested_contacts and not contactAlreadyExists(row["email"]):
                requested_contacts.add(row["email"])
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
                        print(f"Contacts batch of size {len(api_response.results)} pushed successfully.\n")
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
                print(f"Contacts batch of size {len(api_response.results)} pushed successfully.\n")
            except ApiException as e:
                print("Exception when calling batch_api->create: %s\n" % e)

        print(f"{total_contacts_pushed} total contacts pushed.\n")
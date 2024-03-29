# import contacts (after companies), limited to batch sizes of 100
# all contacts need to be in JSON format, associated to company object

import hubspot
import csv
import requests
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
CONTACTS_GET_URL = "https://api.hubapi.com/crm/v3/objects/contacts"
EXISTING_CONTACTS_IN_DB = dict()
COMPANIES_IN_DB = dict()

class HubSpotContactsAPI:
    def __init__(self, access_token, client):
        self.access_token = access_token
        self.client = client
        self.url = "https://api.hubapi.com/crm/v3/objects/contacts"
        self.existing_db_contacts = dict()
        self.size_of_last_push = 0
    
    # request db for info on all existing contacts
    def get_existing_contacts(self):
        params = {"properties": ['email']}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        # make request for all existing contacts in db and filter results to get set with all contact emails
        response = requests.get(self.url, headers=headers, params=params)
        response_data = response.json()
        self.existing_db_contacts = {contact['properties']['email']: contact['id'] for contact in response_data['results']}

        # account for result pagination, get all results
        while ("paging" in response_data):
            response = requests.get(response_data['paging']['next']['link'], headers=headers, params=params)
            response_data = response.json()
            self.existing_db_contacts.update({contact['properties']['email']: contact['id'] for contact in response_data['results']})

    # given a contact email, check if it exists in db already
    def contact_exists_in_db(self, email):
        # be sure to account for case sensitivity
        if email.lower() in self.existing_db_contacts.keys():
            return True
        else:
            return False
    
    # make batch object and call api
    def push_single_batch(self, batch):
        batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=batch)

        try:
            api_response = self.client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
            self.size_of_last_push += len(api_response.results)
            # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
            print(f"Contacts batch of size {len(api_response.results)} pushed successfully.\n")
        except ApiException as e:
            print("Exception when calling batch_api->create: %s\n" % e)
    
    # main function for contacts import from file
    def import_companies_file(self, filename, existing_db_companies):
        # retrieve all existing contacts in db
        print("Retrieving all existing contacts from database...\n")
        self.get_existing_contacts()

        # flow csv data into json format
        print("Flowing in potential new contacts...\n")
        self.size_of_last_push = 0
        with open(filename, newline='') as import_file:
            # variables to keep track of batches
            requested_contacts = set()
            current_batch = list()

            # iterate through contacts file and add unique contacts to batch req
            for row in csv.DictReader(import_file):
                # check if contact has already been seen and/or it already exists in db
                if row['email'] not in requested_contacts and not self.contact_exists_in_db(row['email']):
                    requested_contacts.add(row['email'])
                    current_batch.append({
                        "associations": [{
                            "types": [{
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 1
                            }],
                            "to": {
                                "id": existing_db_companies(row['company domain'])
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

                    # push batch if at batch size limit of 100 and reset batch
                    if len(current_batch) == 100:
                        self.push_single_batch(current_batch)
                        current_batch = list()
            
            # make sure to push leftover/last batch if it didn't hit batch limit of 100
            if len(current_batch) > 0:
                self.push_single_batch(current_batch)

        print(f"{self.size_of_last_push} total contacts pushed.\n")
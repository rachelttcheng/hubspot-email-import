# import contacts (after companies)
# all contacts need to be in JSON format, associated to company object

# url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/create'

import hubspot
import csv
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException

client = hubspot.Client.create(access_token="YOUR_ACCESS_TOKEN")

# do some work here to get contacts into correct JSON format:
#
# contacts = [{
#     "associations":[{
#         "types":[{
#             "associationCategory": "HUBSPOT_DEFINED",
#             "associationTypeId": 0
#         }],
#         "to": {"id":"string"}
#     }],
#     "properties": {
#         "email": "bcooper@biglytics.net",
#         "phone": "(877) 929-0687",
#         "company": "Biglytics",
#         "website": "biglytics.net",
#         "lastname": "Cooper",
#         "firstname":"Bryan"
#     }}]

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
                    "id": "INSERT_ID_HERE"  # should be id of company TO DO
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
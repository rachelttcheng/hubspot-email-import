# import contacts (after companies)
# all contacts need to be in JSON format, associated to company object

# url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/create'

import hubspot
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException

client = hubspot.Client.create(access_token="YOUR_ACCESS_TOKEN")

# ------------------------------------------------------------------------------------------
#                               companies import starts here
# ------------------------------------------------------------------------------------------

# do some work here to get companies into correct JSON format

companies = [{
    "associations":[{
        "types":[{
            "associationCategory":"HUBSPOT_DEFINED",
            "associationTypeId":0
        }],
        "to":{"id":"string"}
    }],
    "properties":{
        "city":"Cambridge",
        "name":"Biglytics",
        "phone":"(877) 929-0687",
        "state":"Massachusetts",
        "domain":"biglytics.net",
        "industry":"Technology"
    }}]

batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies)

try:
    api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling batch_api->create: %s\n" % e)

# ------------------------------------------------------------------------------------------
#                               contacts import starts here
# ------------------------------------------------------------------------------------------

# do some work here to get contacts into correct JSON format

contacts = [{
    "associations":[{
        "types":[{
            "associationCategory": "HUBSPOT_DEFINED",
            "associationTypeId": 0
        }],
        "to": {"id":"string"}
    }],
    "properties": {
        "email": "bcooper@biglytics.net",
        "phone": "(877) 929-0687",
        "company": "Biglytics",
        "website": "biglytics.net",
        "lastname": "Cooper",
        "firstname":"Bryan"
    }}]

batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts)

try:
    api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling batch_api->create: %s\n" % e)
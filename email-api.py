# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# url = 'https://api.hubapi.com/crm/v3/objects/emails'

import hubspot
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException

client = hubspot.Client.create(access_token="YOUR_ACCESS_TOKEN")

batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=[{"associations":[{"types":[{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":0}],"to":{"id":"string"}}],"properties":{"hs_timestamp":"2019-10-30T03:30:17.883Z","hs_email_text":"Thanks for taking your interest let's find a time to connect","hs_email_status":"SENT","hs_email_subject":"Let's talk","hubspot_owner_id":"11349275740","hs_email_to_email":"bh@biglytics.com","hs_email_direction":"EMAIL","hs_email_to_lastname":"Buyer","hs_email_sender_email":"SalesPerson@hubspot.com","hs_email_to_firstname":"Brian","hs_email_sender_lastname":"Seller","hs_email_sender_firstname":"Francis"}}])
try:
    api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling batch_api->create: %s\n" % e)

client = hubspot.Client.create(access_token="YOUR_ACCESS_TOKEN")

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
        "firstname":"Bryan"}
    }]

batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=contacts)


try:
    api_response = client.crm.contacts.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling batch_api->create: %s\n" % e)
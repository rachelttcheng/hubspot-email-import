# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# url = 'https://api.hubapi.com/crm/v3/objects/emails'

import hubspot
import csv
import json
import requests
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException

client = hubspot.Client.create(access_token="YOUR_ACCESS_TOKEN")

# json object hierarchy:
#   - emails array that includes list of email objects (contact to associate emails to)
#       - email objects include two parameters: associations and properties
#           - associations:
#           - properties:
#
# ex:
# emails = [
#     {
#     "associations": [{
#         "types": [{
#             "associationCategory":"HUBSPOT_DEFINED",
#             "associationTypeId":0
#         }],
#         "to": {
#             "id":"string"
#         }},
#     ],
#     "properties": {
#         "hs_timestamp":"2019-10-30T03:30:17.883Z",
#         "hs_email_text":"Thanks for taking your interest let's find a time to connect",
#         "hs_email_status":"SENT",
#         "hs_email_subject":"Let's talk",
#         "hubspot_owner_id":"11349275740",
#         "hs_email_to_email":"bh@biglytics.com",
#         "hs_email_direction":"EMAIL",
#         "hs_email_to_lastname":"Buyer",
#         "hs_email_sender_email":"SalesPerson@hubspot.com",
#         "hs_email_to_firstname":"Brian",
#         "hs_email_sender_lastname":"Seller",
#         "hs_email_sender_firstname":"Francis"
#     }}
# ]

CONTACTS_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"

def getActivityOwner(emailAddress):
    # create query using email and relevant headers
    payload = json.dumps({
        "query": emailAddress
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'YOUR_OAUTH_KEY_HERE'
    }

    # make request
    response = requests.request("POST", CONTACTS_SEARCH_URL, headers=headers, data=payload)

    
    # return ID number of requested email
    return response["results"][0]["id"]

def main():
    # flow csv data into nested json format
    emails = []
    with open("EMAIL_FILE.csv", newline='') as emailsFile:
        emails = [
            {
                "properties": {
                    "hs_timestamp": row["Date"],    # likely needs to be converted to different format
                    "hs_email_text": row["Body"],
                    "hs_email_subject": row["Subject"],
                    "hs_email_headers": json.dumps(
                        {
                            "from": {
                                "email": row["From"]
                            },
                            "to": [
                                {"email": recipient} for recipient in row["To"]
                            ],
                            "cc": [
                                {"email": recipient} for recipient in row["Cc"]
                            ]
                        }
                    )
                },
                "associations": [{
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 198    # 198 is email to contact association
                    }],
                    "to": {
                        "id": getActivityOwner(row['Activity-Assigned-To'])  # id of contact for activity to be associated to
                    }
                }]
            }
            for row in csv.DictReader(emailsFile)
        ]

    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=emails)

    try:
        api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

if __name__ == "__main__":
    main()
# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# url = 'https://api.hubapi.com/crm/v3/objects/emails'

import hubspot
import csv
import json
import requests
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

CONTACTS_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"

# given an email address (unique identifier), make request to hubspot api and get object id
def getActivityOwnerID(emailAddress):
    # create query using email and relevant headers
    payload = json.dumps({
        "query": emailAddress
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN
    }

    # make request
    response = requests.request("POST", CONTACTS_SEARCH_URL, headers=headers, data=payload)

    # TO DO: likely need to handle what happens if no contact found for associated email
    if not response["total"]:
        print(f"{emailAddress} does not exist as contact for email to be associated to\n")
    
    # return ID number of requested email
    return response["results"][0]["id"]

def main():
    # flow csv data into nested json format
    emails = []
    with open("EMAIL_FILE.csv", newline='') as emailsFile:
        emails = [
            {
                "properties": {
                    "hs_timestamp": row["Date"],    # TO DO: likely needs to be converted to different format
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
                        "id": getActivityOwnerID(row['Activity-Assigned-To'])  # id of contact for activity to be associated to
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
# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# url = 'https://api.hubapi.com/crm/v3/objects/emails'

import hubspot
import csv
import json
import requests
from ratelimiter import checkLimit
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
CONTACTS_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

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
    checkLimit()
    response = requests.request("POST", CONTACTS_SEARCH_URL, headers=headers, data=payload)
    responseData = response.json()

    # TO DO: likely need to handle what happens if no contact found for associated email
    if responseData["total"] == 0:
        print(f"{emailAddress} does not exist as contact for email to be associated to\n")
        return emailAddress
    
    # return ID number of requested email
    return responseData["results"][0]["id"]

def main():
    outputFilename = "genesis-capital-output.csv"

    # open a potential "error" file for if an activity-associated email DNE
    errorFilename = outputFilename.split('.')[0] + "-not-uploaded.csv"

    # flow csv data into nested json format
    emails = []
    with open("./" + outputFilename, newline='') as emailsFile:
        emails = list()
        emailReader = csv.DictReader(emailsFile)

        # set up error file by adding "issues" field name
        errorFieldnames = ['issue']
        errorFieldnames.extend(emailReader.fieldnames)
        errorWriter = csv.DictWriter(open(errorFilename, 'w'), fieldnames=errorFieldnames)
        errorWriter.writeheader()

        for row in emailReader:
            activityOwner = getActivityOwnerID(row['Activity-Assigned-To'])

            if not activityOwner.isnumeric():
                row['issue'] = f"{activityOwner} not in contacts"
                errorWriter.writerow(row)
                continue

            emailInstance = {
                "properties": {
                    "hs_timestamp": row["Date"],
                    "hs_email_direction": "INCOMING_EMAIL" if row["X-Gmail-Labels"] == "Incoming" else "FORWARDED_EMAIL",
                    "hs_email_text": row["Body"],
                    "hs_email_subject": row["Subject"],
                    "hs_email_headers": json.dumps(
                        {
                            "from": {
                                "email": row["From"]
                            },
                            "to": [
                                {"email": recipient} for recipient in row["To"].split(";")
                            ],
                            "cc": [
                                {"email": recipient} for recipient in row["Cc"].split(";")
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
                        "id": activityOwner  # id of contact for activity to be associated to
                    }
                }]
            }

            emails.append(emailInstance)

    # create email batch input object and attempt to call api
    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=emails)

    try:
        api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

if __name__ == "__main__":
    main()
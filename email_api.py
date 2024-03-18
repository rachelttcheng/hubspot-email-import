# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# run on command line as such:
# % python3 email-api.py <cleaned csv data filename/path>
# e.g.
# % python3 email-api.py practice-mail-output.csv

import hubspot
import csv
import json
import requests
from ratelimiter import checkLimit
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken
from ast import literal_eval

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

    # if no id found, simply return email address
    if responseData["total"] == 0:
        return emailAddress
    
    # else return found ID number of requested email
    return responseData["results"][0]["id"]

def callEmailAPI(cleanedDataFilename):
    # open a potential "error" file for if an activity-associated email DNE
    errorFilename = cleanedDataFilename.split('.')[0] + "-not-uploaded.csv"

    # flow csv data into nested json format
    emails = []
    with open("./" + cleanedDataFilename, newline='') as emailsFile:
        emails = list()
        emailReader = csv.DictReader(emailsFile)

        # set up error file by adding "issues" field name
        errorFieldnames = ['issue']
        errorFieldnames.extend(emailReader.fieldnames)
        errorWriter = csv.DictWriter(open(errorFilename, 'w'), fieldnames=errorFieldnames)
        errorWriter.writeheader()

        for row in emailReader:
            # create list of associations (email to contact) to put into instance of email to be sent to db
            associations = list()
            for person in literal_eval(row['activity-assigned-to']):
                # grab id number of activity owner, or get email returned
                activityOwner = getActivityOwnerID(person)

                # if no id number found for email within database, it DNE and should be written to error file
                if not activityOwner.isnumeric():
                    row['issue'] = f"{activityOwner} not in contacts"
                    errorWriter.writerow(row)
                    continue
                
                # id exists: include as instance in associations list
                associations.append({
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 198    # email to contact association id as assigned by hubspot
                    }],
                    "to": {
                        "id": activityOwner
                    }
                })

            # create email instance with relative properties from row
            emailInstance = {
                "properties": {
                    "hs_timestamp": row["date"],
                    "hs_email_direction": "INCOMING_EMAIL" if row["x-gmail-labels"] == "Incoming" else "FORWARDED_EMAIL",
                    "hs_email_text": row["body"],
                    "hs_email_subject": row["subject"],
                    "hs_email_headers": json.dumps(
                        {
                            "from": {
                                "email": row["from"]
                            },
                            "to": [
                                {"email": recipient} for recipient in row["to"].split(";")
                            ],
                            "cc": [
                                {"email": recipient} for recipient in row["cc"].split(";")
                            ]
                        }
                    )
                },
                "associations": associations
            }

            emails.append(emailInstance)

    # create email batch input object and attempt to call api
    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=emails)

    try:
        api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
        print(f"\nEmails imported to database. Any emails not able to be imported due to contact not existing have been written to {errorFilename}\n")
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)
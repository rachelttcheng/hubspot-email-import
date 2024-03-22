# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# run on command line as such:
# % python3 email-api.py <cleaned csv data filename/path>
# e.g.
# % python3 email-api.py practice-mail-output.csv

import hubspot
import csv
import json
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken
from ast import literal_eval
from contacts_api import getContacts

ACCESS_TOKEN = fetchToken()
CONTACTS_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
EXISTING_CONTACTS = dict()

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

# given an email address (unique identifier), check against existing contacts fetched from api
def getActivityOwnerID(emailAddress):
    # if no id found, return email address
    if emailAddress not in EXISTING_CONTACTS.keys():
        return emailAddress
    
    # else return ID number of associated contact email
    return EXISTING_CONTACTS[emailAddress]

def callEmailAPI(cleanedDataFilename):
    # open a potential "error" file for if an activity-associated email DNE
    errorFilename = cleanedDataFilename.split('.')[0] + "-not-uploaded.csv"

    # fetch all contacts and their ids from db
    global EXISTING_CONTACTS
    EXISTING_CONTACTS = getContacts()

    # flow csv data into nested json format
    with open("./" + cleanedDataFilename, newline='') as emailsFile:
        emails_batch = list()
        emailReader = csv.DictReader(emailsFile)
        total_emails_pushed = 0
        total_emails_not_pushed = 0

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
                    total_emails_not_pushed += 1
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

            emails_batch.append(emailInstance)

            # push batch if at batch size limit of 100
            if len(emails_batch) == 100:
                batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=emails_batch)

                try:
                    api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                    # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
                    total_emails_pushed += len(api_response.results)
                    print(f"Emails batch of size {len(api_response.results)} pushed successfully.\n")
                except ApiException as e:
                    print("Exception when calling batch_api->create: %s\n" % e)


    # push leftover/last batch if didn't hit batch limit of 100
    if len(emails_batch) > 0:
        batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=emails_batch)

        try:
            api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
            # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
            total_emails_pushed += len(api_response.results)
            print(f"Emails batch of size {len(api_response.results)} pushed successfully.\n")
        except ApiException as e:
            print("Exception when calling batch_api->create: %s\n" % e)
    
    print(f"{total_emails_pushed} emails imported to database.\n{total_emails_not_pushed} email instances were not able to be imported due to an associated contact not existing, and have been written to {errorFilename}\n")
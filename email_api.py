# python program to execute to import emails
# ***ENSURE THAT CONTACTS HAVE BEEN IMPORTED BEFORE CALLING THIS PROGRAM

# run on command line as such:
# % python3 email-api.py <cleaned csv data filename/path>
# e.g.
# % python3 email-api.py practice-mail-output.csv

import hubspot
import csv
import json
import time
from pprint import pprint
from hubspot.crm.objects.emails import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken
from ast import literal_eval
from companies_api import getCompanies
from contacts_api import getContacts, pushContactsBatch

ACCESS_TOKEN = fetchToken()
CONTACTS_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"
EXISTING_CONTACTS = dict()
EXISTING_COMPANIES = dict()

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

# given an email address (unique identifier), check against existing contacts fetched from api
def getActivityOwnerID(emailAddress):
    # if no id found, return email address
    if emailAddress not in EXISTING_CONTACTS.keys():
        return emailAddress
    
    # else return ID number of associated contact email
    return EXISTING_CONTACTS[emailAddress]

# go through csv and add any contacts not already in database whose domain does exist in database
def pushNewContacts(cleanedDataFilename):
    # fetch all existing companies and contacts
    global EXISTING_COMPANIES
    global EXISTING_CONTACTS
    EXISTING_COMPANIES = getCompanies()
    EXISTING_CONTACTS = getContacts()
    print(f"existing contacts: {EXISTING_CONTACTS.keys()}\n")
    print(f"existing companies: {EXISTING_COMPANIES.keys()}\n")

    contacts_batch = list()
    total_contacts_pushed = 0

    with open(cleanedDataFilename, newline='') as emailsFile:
        emailReader = csv.DictReader(emailsFile)
        for row in emailReader:
            for person in literal_eval(row['activity-assigned-to']):
                print(f"checking {person}")
                _, companyDomain = person.split('@')
                print(f"company domain: {companyDomain}")

                # if not already existing contact, but the company domain exists in db, add as a new contact to push
                if person not in EXISTING_CONTACTS.keys() and companyDomain in EXISTING_COMPANIES.keys():
                    contacts_batch.append({
                        "associations": [{
                            "types": [{
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 1
                            }],
                            "to": {
                                "id": EXISTING_COMPANIES["company domain"]
                            }
                        }],
                        "properties": {
                            "email": person,
                            "website": companyDomain
                        }
                    })

                    # make call to create contacts if batch size hit
                    if len(contacts_batch) == 100:
                        total_contacts_pushed += pushContactsBatch(contacts_batch)

                        # reset batch
                        contacts_batch = list()
        
        # make residual call
        if len(contacts_batch) > 0:
            total_contacts_pushed += pushContactsBatch(contacts_batch)
        
        print(f"{total_contacts_pushed} total contacts pushed to database before email push.\n")

def pushEmailBatch(emails_batch):
    # create batch object
    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=emails_batch)

    try:
        api_response = client.crm.objects.emails.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
        print(f"Emails batch of size {len(api_response.results)} pushed successfully.\n")
        return len(api_response.results)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

def callEmailAPI(cleanedDataFilename):
    # first, push any relevant contacts that might not already exist in db
    pushNewContacts(cleanedDataFilename)

    # wait between api calls so that when emails are created, ensure additional contacts already exist in the db
    print("Waiting 10 seconds for new contacts to populate database before importing email...\n")
    for i in range(10, 0, -1):
        print(i)
        time.sleep(1)

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

                # if no id number found for email within database, look at next person
                if not activityOwner.isnumeric():
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

            # if no one from database is associated with email, write the row to the error file and don't create an email instance
            if len(associations) == 0:
                row['issue'] = f"No one in {row['activity-assigned-to']} exists as a contact in Hubspot database for activity to be assigned to"
                errorWriter.writerow(row)
                total_emails_not_pushed += 1

                continue

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
                total_emails_pushed += pushEmailBatch(emails_batch)
                emails_batch = list()   # reset batch

    # push leftover/last batch if didn't hit batch limit of 100
    if len(emails_batch) > 0:
        total_emails_pushed += pushEmailBatch(emails_batch)
    
    print(f"{total_emails_pushed} emails imported to database.\n{total_emails_not_pushed} email instances were not able to be imported due to an associated contact not existing, and have been written to {errorFilename}\n")
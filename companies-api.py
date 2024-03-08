# create/update companies before contacts
# url = 'https://api.hubapi.com/crm/v3/objects/companies/batch/create'

import hubspot
import csv
from pprint import pprint
from hubspot.crm.companies import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

def main():
    # flow company info into json format
    companies = []
    with open("CONTACTS_FILE.csv", newline='') as contactsFile:
        companies = [
            {
                "properties": {
                    "domain": row["company domain"]
                }
            }
            for row in csv.DictReader(contactsFile)
        ]

    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies)

    try:
        api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling batch_api->create: %s\n" % e)

if __name__ == "__main__":
    main()
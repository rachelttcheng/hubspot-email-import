# import contacts (after companies)
# all contacts need to be in JSON format, associated to company object

# url = 'https://api.hubapi.com/crm/v3/objects/contacts/batch/create'

import hubspot
import csv
import requests
import json
import time
from pprint import pprint
from hubspot.crm.contacts import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
RATE_LIMIT_PER_SEC = 10

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

COMPANY_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/companies/search"

# rate limiter for querying api for match for company domain
class rateLimiter():
    def __init__(self, rate_limit_per_second):
        self.rate_limit_per_second = rate_limit_per_second
        self.last_called = 0
    
    def callAPI(self, companyDomain):
        # space out calls, based on time since last call
        now = time.time()
        time_since_last_call = now - self.last_called
        if (time_since_last_call < (1 / self.rate_limit_per_second)):
            time.sleep(1 / (self.rate_limit_per_second - time_since_last_call))
        
        # return response data from making request
        return self.make_api_request(companyDomain)

    def make_api_request(self, company_domain):
        # insert company domain into query and create relevant headers
        payload = json.dumps({"query": company_domain})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + ACCESS_TOKEN
        }

        # make request
        response = requests.request("POST", COMPANY_SEARCH_URL, headers=headers, data=payload)
        responseData = response.json()

        # return data
        return responseData

caller = rateLimiter(rate_limit_per_second=10)

# given a company domain (unique identifier), makes request to hubspot api and returns object id within hubspot databse
def getAssociatedCompanyID(companyDomain):
    # get response data, with rate limiting
    responseData = caller.callAPI(companyDomain)
    print(responseData)

    # handle if no result; still TO DO in regards to if program should terminate or not
    if responseData["total"] == 0:
        print(f"Company {companyDomain} does not exist, cannot associate to contact\n")

    # return company id
    return responseData["results"][0]["id"]

def main():
    # flow csv data into nested json format
    contacts = []
    with open("sample-contacts.csv", newline='') as contactsFile:
        contacts = [
            {
                "associations": [{
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 1
                    }],
                    "to": {
                        "id": getAssociatedCompanyID(row["company domain"])
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

if __name__ == "__main__":
    main()
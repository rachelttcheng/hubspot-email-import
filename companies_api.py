# create/update companies before contacts, in batches of 100 (size limit)
# url = 'https://api.hubapi.com/crm/v3/objects/companies/batch/create'

import hubspot
import csv
import requests
from pprint import pprint
from hubspot.crm.companies import BatchInputSimplePublicObjectInputForCreate, ApiException
from get_token import fetchToken

ACCESS_TOKEN = fetchToken()
COMPANIES_GET_URL = "https://api.hubapi.com/crm/v3/objects/companies"
EXISTING_COMPANIES_IN_DB = dict()

client = hubspot.Client.create(access_token=ACCESS_TOKEN)

# make api call to get list of existing companies
def getCompanies():
    params =  {"properties": ["domain"]}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN
    }

    # make request for all existing companies in db and filter results to get dict with {company domain: company id} key value pairs
    response = requests.get(COMPANIES_GET_URL, headers=headers, params=params)
    responseData = response.json()
    all_results = {company['properties']['domain']: company['id'] for company in responseData['results']}

    # account for result pagination, get all results
    while ("paging" in responseData):
        response = requests.get(responseData['paging']['next']['link'], headers=headers, params=params)
        responseData = response.json()
        all_results.update({company['properties']['domain']: company['id'] for company in responseData['results']})

    return all_results

# given company domain, checks if it already exists within database to prevent duplicates
def companyExists(companyDomain):
    if companyDomain in EXISTING_COMPANIES_IN_DB.keys():
        return True
    else:
        return False

# main function for file; makes 
def callCompaniesAPI(contactsFilename):
    # retrieve all existing companies within db and assign to global variable set
    global EXISTING_COMPANIES_IN_DB
    EXISTING_COMPANIES_IN_DB = getCompanies()
    print(EXISTING_COMPANIES_IN_DB)

    # flow company info into json format
    with open(contactsFilename, newline='') as contactsFile:
        # variables to keep track of batches
        requested_companies = set()
        companies_batch = list()
        total_companies_pushed = 0

        # iterate through csv file and add companies that don't already exist, either within local companies list or hubspot databse into batch request
        for row in csv.DictReader(contactsFile):
            # check if company already exists within larger file set, then check if it already exists within hubspot database
            if row["company domain"] not in requested_companies and not companyExists(row["company domain"]):
                requested_companies.add(row["company domain"])
                companies_batch.append({"properties": {"domain": row["company domain"]}})

                # push batch if size is at limit of 100
                if len(companies_batch) == 100:
                    batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies_batch)

                    try:
                        api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                        total_companies_pushed += len(api_response.results)
                        # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
                        print(f"Company batch of size {len(api_response.results)} pushed successfully.")
                    except ApiException as e:
                        print("Exception when calling batch_api->create: %s\n" % e)

                    # reset batch
                    companies_batch = list()

        # make sure to push leftover/last batch if it didn't hit batch limit of 100
        if len(companies_batch) > 0:
            batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=companies_batch)

            try:
                api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
                total_companies_pushed += len(api_response.results)
                # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
                print(f"Company batch of size {len(api_response.results)} pushed successfully.\n")
            except ApiException as e:
                print("Exception when calling batch_api->create: %s\n" % e)

        print(f"{total_companies_pushed} total companies pushed successfully.\n")

        return total_companies_pushed
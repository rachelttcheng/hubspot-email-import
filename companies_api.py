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

class HubSpotCompaniesAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.url = "https://api.hubapi.com/crm/v3/objects/companies"
        self.existing_db_companies = dict()
        self.size_of_last_push = 0

    # make api call to get list of existing companies and update self.existing_db_companies
    def get_existing_companies(self):
        params = {"properties": ["domain"]}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        # make request for all existing companies in db and filter results to get dict with {company domain: company id} key value pairs
        response = requests.get(self.url, headers=headers, params=params)
        response_data = response.json()
        self.existing_db_companies = {company['properties']['domain']: company['id'] for company in response_data['results']}

        # account for result pagination, get all results
        while ('paging' in response_data):
            response = requests.get(response_data['paging']['next']['link'], headers=headers, params=params)
            response_data = response.json()
            self.existing_db_companies.update({company['properties']['domain']: company['id'] for company in response_data['results']})
        
    # given company domain, checks if it already exists within database to prevent duplicates
    def company_exists_in_db(self, company_domain):
        # account for case sensitivity
        if company_domain.lower() in self.existing_db_companies.keys():
            return True
        else:
            return False
    
    # make batch object and call api
    def push_single_batch(self, batch):
        batch_input_simple_public_object_input_for_create = BatchInputSimplePublicObjectInputForCreate(inputs=batch)

        try:
            api_response = client.crm.companies.batch_api.create(batch_input_simple_public_object_input_for_create=batch_input_simple_public_object_input_for_create)
            self.size_of_last_push += len(api_response.results)
            # pprint(api_response) # -- UNCOMMENT IF WANT MORE DETAILED RESPONSE INFO
            print(f"Company batch of size {len(api_response.results)} pushed successfully.")
        except ApiException as e:
            print("Exception when calling batch_api->create: %s\n" % e)
    
    # main function for company import from file
    def import_companies_file(self, filename):
        # retrieve all existing companies in db
        print("Retrieving existing companies from database...\n")
        self.get_existing_companies()

        # flow company info into json format
        print("Flowing in potential new companies...\n")
        with open(filename, newline='') as import_file:
            # variables to keep track of batches
            requested_companies = set()
            current_batch = list()

            # iterate through csv file and add companies that haven't already been seen and/or already exist in db
            for row in csv.DictReader(import_file):
                # check if company already seen; then check if exists within larger db
                if row['company domain'] not in requested_companies and not self.company_exists_in_db(row['company domain']):
                    requested_companies.add(row['company domain'])
                    current_batch.append({"properties": {"domain": row['company domain']}})

                # push batch if size is at limit of 100, then reset it
                if len(current_batch) == 100:
                    self.push_single_batch(current_batch)
                    current_batch = list()
        
            # push leftover/last batch if necessary
            if len(current_batch) > 0:
                self.push_single_batch(current_batch)
        
        print(f"{self.size_of_last_push} total companies pushed.\n")
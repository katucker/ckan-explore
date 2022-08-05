"""Python command line script for querying the packages in a CKAN instance..
 This program will conduct a query and return only a specific set of fields.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for 
 the URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for
 input if the environment variable is not set.
 
 The program accepts a variable number of command line arguments.
 The first argument is a query string to use in conducting the search.
 The remaining arguments are the names of the fields to include in the
 query results.
 
 Note that any fields added to the extras portion of the CKAN schema can
 be referenced in the return field list by prefacing the field name with
 "extras_".
 
 Example: Query for a package with id "9dc70e6b-8426-4d71-b9d5-70ce6094a3f4"
 and returning only the id, name, title and extras field named "bureau_code":
     
     python package_search.py id:9dc70e6b-8426-4d71-b9d5-70ce6094a3f4 id name\
       title extras_bureau_code
       
  Example: Find all packages for which the extras data_quality field is false,
  and return the id, name and title.
  
    python package_search.py extras_data_quality:false id name title

"""
import json
import logging
import os
import sys
import re

from ckanapi import RemoteCKAN

def do_package_search(ckan_connection, search_term = "*:*", field_list = None):
    result = None
    limit = 10
    try:
        result = ckan_connection.call_action(action='package_search', data_dict={
            'rows': limit,
            'start': 0,
            'include_private': True,
            'include_drafts': True,
            'q': search_term,
            'fl': field_list
            })
    except:
        return result

    return result.get('results',None)
 	
if __name__ == '__main__':

    url = os.getenv('ED_CKAN_URL', None)
    api_key = os.getenv('ED_CKAN_KEY', None)

    errors = []

    if not url:
        errors.append('ED_CKAN_URL environment variable is needed.')
    if not api_key:
        errors.append('ED_CKAN_KEY environment variable is needed.')

    search_text = "*:*"
    field_list = []
    if len(sys.argv) > 1:
        search_text = sys.argv[1]
    for arg in sys.argv[2:]:
        field_list.append(arg)
        
    if len(errors):
        for e in errors:
            logging.error(e)
        sys.exit(1)

    remote_ckan = RemoteCKAN(address=url, apikey=api_key)

    # Perform the package search.
    dataset_list = do_package_search(remote_ckan, search_text, field_list)

    print(json.dumps(dataset_list, indent=2))
    

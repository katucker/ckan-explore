"""Python command line script for querying the resources in a CKAN instance..
 This program will conduct a query and print a subset of the data found.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for 
 the URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for
 input if the environment variable is not set.
 
 The program accepts a single command line argument, the query string to 
 use in conducting the search.
 
 Note that any fields added to the extras portion of the CKAN schema can
 be referenced in the return field list by prefacing the field name with
 "extras_".
 
 Example: Query for a resource with id "9dc70e6b-8426-4d71-b9d5-70ce6094a3f4".
     
     python resource_search.py id:9dc70e6b-8426-4d71-b9d5-70ce6094a3f4
       
  Example: Find all resources for which the extras data_quality field is false.
  
    python resource_search.py extras_data_quality:false

"""
import json
import logging
import os
import sys
import re

from ckanapi import RemoteCKAN

def do_resource_search(ckan_connection, search_term = "*:*"):
    result = None
    try:
        result = ckan_connection.call_action(action='resource_search', data_dict={
            'query': search_term
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
    if len(sys.argv) > 1:
        search_text = sys.argv[1]
    else:
        errors.append('No query string specified on command line.')
        
    if len(errors):
        for e in errors:
            logging.error(e)
        sys.exit(1)

    remote_ckan = RemoteCKAN(address=url, apikey=api_key)

    # Perform the package search.
    resource_list = do_resource_search(remote_ckan, search_text)

    print(json.dumps(resource_list, indent=2))
    

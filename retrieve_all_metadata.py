"""Python command-line script for retrieving metadata from CKAN.
 This script creates a local JSON file containing the aggregate metadata from
 a CKAN repository. The JSON file can then be used for offline processing, such as
 generating reports.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for the
 URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for input
 if the environment variable is not set.
 
 """
import getpass
import logging
import os
import sys

import ckanapi
import json


def retrieve_metadata(connection):
    """Retrieve the metadata in the connected CKAN repository.
    """
    result = []
    try:
        offset = 0
        increment = 1000
        while (True):
#        while (offset < increment):
            pass_data_dict = { "limit": increment, "offset": offset }
            pass_result = connection.call_action(action='current_package_list_with_resources', data_dict=pass_data_dict)
            if len(pass_result) == 0: break
            offset += increment
            for dataset in pass_result:
                result.append(dataset)
            logging.info('Retrieving from offset %d', offset)
        return result
    except Exception as e:
        logging.info(e)
        return result

def unravel_metadata(amd):
    for dataset in amd:
        if dataset.get("extras",None) is not None:
            for extra in dataset["extras"]:
                dataset[extra["key"]] = extra["value"]
            dataset.pop("extras")
        if dataset.get("organization",None) is not None:
            dataset["org_id"] = dataset["organization"].get("id",None) 
            dataset["org_name"] = dataset["organization"].get("name",None)
            dataset.pop('organization')
        if dataset.get("tags",None) is not None:
            dataset["taglist"] = []
            for tag in dataset["tags"]:
                dataset["taglist"].append(tag["display_name"])
            dataset.pop("tags")
        if dataset.get("groups",None) is not None:
            dataset["grouplist"] = []
            for group in dataset["groups"]:
                dataset["grouplist"].append(group["display_name"])
            dataset.pop("groups")
        if dataset.get("relationships_as_object", None) is not None:
            dataset.pop("relationships_as_object")
    return amd
    
    
if __name__ == '__main__':

    logging.basicConfig(level=os.environ.get("LOGLEVEL",logging.INFO))
    
    # Retrieve the URL and API Key from environment variables, if set.
    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    # Prompt for the API connection details if missing.
    if not url:
        url = input('Enter CKAN URL:')
    if not api_key:
        api_key = getpass.getpass('Enter CKAN API key:')

    remote = ckanapi.RemoteCKAN(url, api_key)

    output_file_name = ''
    if len(sys.argv) > 1:
        output_file_name = sys.argv[1]
    else:
        output_file_name = input('Enter output file name:')

    with open(output_file_name, "w") as output_file:
        output_file.write(json.dumps(unravel_metadata(retrieve_metadata(remote)), indent=2))

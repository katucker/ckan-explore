"""Python command-line script for comparing data files listed in a CKAN instance
with data files listed in a JSON file, to identify potential duplicates.
 This script outputs a list of identifying information from the CKAN instance
 and the input JSON file, to use in validating whether the data files are
 genuinely the same.
 The purpose of this comparison is to de-duplicate datasets created from
 multiple sources. The same data file may be referenced in both the CKAN
 instance and the JSON file, but with different title, description or
 even URL. This script identifies data files that appear to have the
 same content, and thus warrant additional scrutiny.
 The JSON input file is assumed to be compliant with the DCAT-US schema
 version 1.1.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for the
 URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. The value for the API key will be prompted for input
 if the environment variable is not set.

 A single command line argument may be provided, naming the JSON file to
 use for comparison. The file name will be prompted for input if not
 provided on the command line.
 
 """
import getpass
import hashlib
import json
import logging
import os
import requests
import sys

import ckanapi

def get_hash(url):
    try:
        # Initialize the hash object.
        hash = hashlib.sha512()
        # Retrieve the file at the passed URL as a stream, 
        # in case it is larger than will fit in memory.
        response = requests.get(url, stream=True)
        # Read the stream, using whatever chunk size is used in the 
        # network messages, updating the hash object for each one received.
        for buff in response.iter_content(chunk_size=None):
            if buff:
                hash.update(buff)
        return hash.digest()
    except Exception as e:
        logging.error(e)
        return null


def get_resource_fingerprints(connection):
    """Retrieve the metadata for all datasets in the connected CKAN repository.
    """
    metadata = {}
    try:
        offset = 0
        increment = 1000
        while (True):
            pass_data_dict = { "limit": increment, "offset": offset }
            pass_result = connection.call_action(action='current_package_list_with_resources', data_dict=pass_data_dict)
            if len(pass_result) == 0: break
            offset += increment
            # Iterate over the retrieved datasets.
            for dataset in pass_result:
                if ('type' in dataset and dataset['type'] == "dataset"):
                    if 'resources' in dataset:
                        for resource in dataset['resources']:
                            if 'url' in resource:
                                hash = get_hash(resource['url'])
                                if hash:
                                    metadata[hash] = {"title": dataset['name'], "dataset_id": dataset['id'],"resource_id": resource['id'], "url": resource['url']}

            logging.info('Retrieving from offset %d', offset)
        return metadata
    except Exception as e:
        logging.error(e)
        return metadata
    
    
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
        input_file_name = sys.argv[1]
    else:
        input_file_name = input('Enter name for JSON comparison file:')

    with open(input_file_name, "rt") as input_file:
        ckan_metadata = get_resource_fingerprints(remote)
        dcatus = json.load(input_file)
        print('CKAN dataset id, resource id, URL, JSON dataset id, URL, CKAN title, JSON title')
        for dataset in dcatus['dataset']:
            if 'distribution' in dataset:
                for distribution in dataset['distribution']:
                    if 'downloadURL' in distribution:
                        dcathash = get_hash(distribution['downloadURL'])
                        if dcathash and dcathash in ckan_metadata:
                            match = ckan_metadata[dcathash]
                            print(f"{match['datasetid']}, {match['resourceid']}, {match['url']}, {dataset['identifier']},{distribution['downloadURL']}, {match['title']},{dataset['title']}")

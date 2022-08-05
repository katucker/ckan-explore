import json
import logging
import os
import sys
import re

from ckanapi import RemoteCKAN

def do_dataset_dump(ckan_connection, id):
    result = None
    data_dict = { 'id': id }
    try:
        result = ckan_connection.call_action(action='package_show',
                                             data_dict=data_dict)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print('Failed to retrieve dataset.\n,Exception: %s'.format(e))
 	
if __name__ == '__main__':

    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    errors = []

    if not url:
        errors.append('CKAN_URL environment variable is needed.')
    if not api_key:
        errors.append('CKAN_KEY environment variable is needed.')

    if len(sys.argv) > 1:
        id = sys.argv[1]
    else:
        errors.append('Provide a command line argument of the dataset identifier or name')
        
    if len(errors):
        for e in errors:
            logging.error(e)
        sys.exit(1)

    remote_ckan = RemoteCKAN(address=url, apikey=api_key)

    do_dataset_dump(remote_ckan, id)

    

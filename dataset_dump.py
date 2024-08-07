import argparse
import configparser
import json
import logging
import os
import sys
import re

from ckanapi import RemoteCKAN

_DEFAULT_CONFIG="ckan-explore.ini"

def do_dataset_dump(ckan_connection, id):
    result = None
    data_dict = { 'id': id }
    try:
        result = ckan_connection.call_action(action='package_show',
                                             data_dict=data_dict)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logging.exception(f'Failed to retrieve dataset {id}.')
 	
if __name__ == '__main__':

    logging.basicConfig(level=os.environ.get("LOGLEVEL",logging.ERROR))
    
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Retrieve and print all the metadata for a specified dataset.''')
    ap.add_argument('id', help='Identifier for the dataset to dump.')
    ap.add_argument('-c','--config', help='Name of the configuration file to use.', default=_DEFAULT_CONFIG)
    args = ap.parse_args()

    cp = configparser.ConfigParser()
    cp.read(args.config)

    url = cp.get('remote','CKAN_URL', fallback=None)
    api_key = cp.get('remote','CKAN_KEY', fallback=None)

    # Set the logging level, looking first in the configuration file,
    # then in the environment, and finally defaulting to logging only
    # errors.
    logging.basicConfig(level = cp.get('logging', 'LOGLEVEL', 
        fallback = os.getenv('LOGLEVEL', logging.ERROR)))
    

    errors = []

    if url is None:
        errors.append(f'CKAN API URL not specified in configuration file {args.config}.')
    if api_key is None:
        logging.warning(f'CKAN API key not specified in configuration file {args.config}. Using anonymous access.')

    if len(errors):
        for e in errors:
            logging.error(e)
        sys.exit(1)

    remote_ckan = RemoteCKAN(address=url, apikey=api_key)

    do_dataset_dump(remote_ckan, args.id)

    

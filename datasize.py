"""Python command-line script for summing the size of resources referenced in a CKAN instance.
 This script scans all the resources in a CKAN repository, and retrieves the size of each
 downloadable data file referenced.

 The base URL for the API to use (without the trailing "/api/action" text)
 can be specified in an environment variable named 'CKAN_URL'. The value for the
 URL will be prompted for input if the environment variable is not set.

 The API key to use for authentication can be specified in an environment
 variable named 'CKAN_KEY'. If the environment variable is not set, only
 anonymous access is used, resulting in only the publicly-available resources
 being included in the sum.
 
 """
import argparse
import logging
import os
import re
import sys

import ckanapi
import requests


def sum_resource_size(connection, timeout, filter):
    """Retrieve the metadata in the connected CKAN repository.
    """
    sum = 0
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
                if dataset.get('type', None) != 'dataset':
                    continue
                for resource in dataset.get('resources',[]):
                    url = resource.get("url", None)
                    if url is not None:
                        if filter is not None:
                            if re.search(f'^{filter}', url) is None:
                                logging.info('Skipping %s', url)
                                continue
                            else:
                                logging.info('Checking %s', url)
                    size = resource.get("size", None)
                    if size is not None:
                        sum += size
                    else:
                            try:
                                response = requests.head(url,allow_redirects=True, timeout=timeout)
                                if response is not None:
                                    if response.status_code != 200:
                                        continue
                                    size = response.headers.get('content-length', None)
                                    if size is not None:
                                        sum += int(size)
                            except Exception:
                                continue

        return sum
    except Exception as e:
        logging.info('Error scanning CKAN resources.', exc_info=e)
        return sum

    
if __name__ == '__main__':

    logging.basicConfig(level=os.environ.get("LOGLEVEL",logging.INFO))
    
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Sum the size of files referenced in a CKAN insstance.
''',
        epilog='''The program uses environment variables for optionally authenticating CKAN access.
        CKAN_URL specifies the base URL for the CKAN instance. The user is prompted to provide a
        URL at runtime if the environment variable is not set.
        CKAN_KET specifies an API key for privileged access to the CKAN instance. Anonymous access 
        is used if the environment variable is not set.
''')
    ap.add_argument('-t', '--timeut', dest='timeout', default=5, type=int,
        help='The number of seconds to wait for URL headers.')
    ap.add_argument('-f','--filter', dest='filter', default=None,
        help='A URL for filtering resources. Only the resources starting with the specified URL will be included in the sum.')
    args = ap.parse_args()

    # Retrieve the URL and API Key from environment variables, if set.
    url = os.getenv('CKAN_URL', None)
    api_key = os.getenv('CKAN_KEY', None)

    # Prompt for the API connection details if missing.
    if not url:
        url = input('Enter CKAN URL:')

    remote = None
    if api_key is not None:
        remote = ckanapi.RemoteCKAN(url, api_key)
    else:
        remote = ckanapi.RemoteCKAN(url)

    sum = sum_resource_size(remote, args.timeout, args.filter)
    print(f'Total size of referenced datafiles: {sum} bytes')

import getpass
import json
import logging
import os
import argparse

import requests

base_url = "https://api.gsa.gov/analytics/dap/v2.0.0/"

action = "agencies/education/reports/"

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Retrieve website statistics from the Digital Analytics Program API.
''',
        epilog='''The program uses an environment variable named DAP_KEY for authenticating access.
        If the environment variable is not set, the key value to use will be requested at runtime.
''')
    ap.add_argument('-a', '--after', dest='after_date',
        help='The date to use for the start date of the web statistics, in YYYY-MM-DD format')
    ap.add_argument('-b', '--before', dest='before_date',
        help='The date to use for the end date of the web statistics, in YYYY-MM-DD format'),
    ap.add_argument('-r', '--report', dest='report', default='site',
        choices = ['download','domain','site','traffic-source'],
        help='The report name to retrieve.')
    ap.add_argument('-p', '--page', dest='page', type=int,
        help='The report page to retrieve.')
    ap.add_argument('-l', '--limit', dest='limit', type=int,
        help='The maximum number of responses to include in the report, capped at 10,000.')
    
    args = ap.parse_args()

    params = {}
    if args.after_date is not None:
        params['after'] = args.after_date
    if args.before_date is not None:
        params['before'] = args.before_date
    if args.page is not None:
        params['page'] = args.page
    if args.limit is not None:
        params['limit'] = args.limit
    if args.report is not None:
        detail = f"{args.report}/data"

    # Retrieve the API Key from the environment variable, if set.
    api_key = os.getenv('DAP_KEY', None)

    # Prompt for the API connection details if missing.
    if not api_key:
        api_key = getpass.getpass('Enter DAP API key:')

    headers = {"x-api-key": api_key}

    api_call = f'{base_url}{action}{detail}'
    print(api_call)
    result = requests.get(api_call, headers=headers, params=params)

    if result.status_code == 200:
        interpreted_result = json.loads(result.text)
        print(json.dumps(interpreted_result, indent=2))
    else:
        print(result.status_code)
        print(result.text)



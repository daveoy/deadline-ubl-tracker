#!/usr/bin/env python3

'''
    This script uses environment varables for server ID and password
    so it shouldn't be left around either in command histroy or in
    your envronment. Because of this, it's best to clean up your shell
    on Mac/Linux like so:

    ```
        export FNO_SERVER=ABCD12345678
        read -s FNO_PASSWORD && export FNO_PASSWORD
        chmod +x ./license-counts.py
        ./license-counts.py
        unset FNO_PASSWORD
    ```

    On Windows, make sure to use Command Prompt instead of PowerShell and
    do this:
    ```
        set FNO_SERVER=ABCD12345678
        set FNO_PASSWORD=some+great+password!
        python3 license-counts.py
        set FNO_PASSWORD=
    ```
'''

import os
import requests
import time
from prometheus_client import Gauge, start_http_server

SITE_ID = 'thinkbox.compliance.flexnetoperations.com'
SERVER_ID = os.environ['FNO_SERVER']
SERVER_BASE_URL = 'https://{0}/api/1.0/instances/{1}'.format(SITE_ID, SERVER_ID)
SERVER_LOGIN_URL = SERVER_BASE_URL + '/authorize'
SERVER_FEATURE_SUMMARY_URL = SERVER_BASE_URL + '/features/summaries'

login_dict = {
    'user': 'admin',
    'password': os.environ['FNO_PASSWORD']
}

g = Gauge('thinkbox_ubl', 'ubl details as reported by thinkbox',['feature','entitlement'])
PORT = int(os.getenv("LISTEN_PORT",9666))
print("starting server on port {}".format(PORT))
start_http_server(PORT)

while True:
    session = requests.Session()

    try:
        login_request = session.post(SERVER_LOGIN_URL, json = login_dict).json()
    except Exception as e:
        print("Error when trying to log in: {}".format(str(e)))

    auth_token = login_request['token']

    auth_header = {
        'Authorization': 'Bearer {}'.format(auth_token)
    }

    try:
        data = session.get(url=SERVER_FEATURE_SUMMARY_URL, headers=auth_header).json()
    except Exception as e:
        print("Error while collecting capabilities: {}".format(e))

    for feature_name, value in data.items():
        # We only have one version of any license
        value = value['0.00']

        print("Feature:       {:} ".format(feature_name))
        print("    Entitled:  {:,}".format(int(value['totalCount'])))
        g.labels(feature_name,"entitled").set(int(value['totalCount']))
        print("    Used:      {:,}".format(int(value['totalUsed'])))
        g.labels(feature_name,"used").set(int(value['totalUsed']))
        print("    Overage:   {:,}".format(int(value['totalOverdraftCount'])))
        g.labels(feature_name,"overage").set(int(value['totalOverdraftCount']))
        print("    Available: {:,}".format(int(value['totalAvailable'])))
        g.labels(feature_name,"available").set(int(value['totalAvailable']))
        print()
    time.sleep(30)
from sys import argv
import requests
import os
import json

# api-endpoint
ENDPOINT = "10.0.7.253:9443"
LOGIN_URL = "https://"+ENDPOINT+"/portal/api/v1/login/direct"

def main():
    # check args
    if (len(argv)<3):
        print("usage -- python caller.py <iem_user> <iem_password>")
        return
    
    API_NAME = argv[1]
    API_PWD = argv[2]

    login_data = {'username':API_NAME,
        'password':API_PWD}
    login_headers = {'content-type': 'application/json'}
    getDevices_headers = {'accept-language': 'en-US', 'authorization' : ''}

    # POST login
    r_login = requests.post(url = LOGIN_URL, data=json.dumps(login_data), headers=login_headers, verify=False)
  
    # check return value
    if (r_login.status_code!=200):
        print("Something went wrong. Error code = "+r_login.status_code)
        return

    # extracting token
    api_access_token = r_login.json()["data"]["access_token"]
    print("The received token is: %s" %str(api_access_token))
    getDevices_headers['authorization'] = api_access_token

    # GET devices 

if __name__ == "__main__":
    main()
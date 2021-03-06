from sys import argv
import requests
import os
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# api-endpoint
# TODO check API new version
MAN_ENDPOINT = "10.0.7.253:9443"
DEV_ENDPOINT = "10.0.7.132:8083"
LOGIN_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/login/direct"
LS_DEV_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/devices"
LS_APP_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/devices/installed-apps?"
LS_JOBS_URL = ""
DEPLOY_URL = "http://"+DEV_ENDPOINT+"/deploy"
APP_TO_CHECK = "helloworld"
APP_VER = "0.0.1"

def main():
    # check args
    if (len(argv)<3):
        print("usage -- python caller.py <iem_user> <iem_password>")
        return    
    API_NAME = argv[1]
    API_PWD = argv[2]

    # HEADERS and PAYLOADS (as Python dictionary)
    login_data = {'username':API_NAME,
        'password':API_PWD}
    login_headers = {'content-type': 'application/json'}
    getDevices_headers = {'accept-language': 'en-US', 'authorization' : ''}
    deploy_data = {'name' : APP_TO_CHECK, 'version' : APP_TO_CHECK, 'platform' : 'siemens'}
    deploy_files = {'file' : open('./compose.yml','rb')}

    # POST login
    r_login = requests.post(url = LOGIN_URL, data=json.dumps(login_data), headers=login_headers, verify=False)
  
    # check return value
    if (r_login.status_code!=200):
        print("Something went wrong. Error code = "+r_login.status_code)
        return

    # extracting token
    api_access_token = r_login.json()["data"]["access_token"]
    print("\nThe token is: %s\n" %str(api_access_token))
    getDevices_headers['authorization'] = api_access_token

    # GET devices (ASSUMPTION ONE --> I consider the first ([0]) device of the list)
    # --- 08efe36153fb4e559c3e8ffcbe9b6ccc ---
    r_devices = requests.get(url = LS_DEV_URL, headers=getDevices_headers, verify=False)
    deviceId = r_devices.json()["data"][0]["deviceId"]
    print("\nThe deviceID is: %s\n" %deviceId)
    
    # # GET installed apps on device
    r_apps = requests.get(url = LS_APP_URL+"deviceid="+deviceId, headers=getDevices_headers, verify=False)
    for a in r_apps.json()["data"]:
        # print(a["title"]) #DEBUG
        if (a["title"]==APP_TO_CHECK): #app already installed
            print("App "+APP_TO_CHECK+" already installed. EXIT.")
            return
    
    # app is not here! --> START TIMER --> deploy
    start = time.time()
    r_deploy = requests.post(url = DEPLOY_URL, files = deploy_files, data=deploy_data, verify=False)
    print(r_deploy.json())
    if(r_deploy.status_code!=200):
        print("Something went wrong. Error code: "+r_deploy.status_code)
        return

    # check installed app
    # ASSUMPTION TWO --> cannot find a "GET jobs" - I use the List Apps to check the installation
    r_apps = requests.get(url = LS_APP_URL+"deviceid="+deviceId, headers=getDevices_headers, verify=False)
    counter=0
    while (r_apps.text.find(APP_TO_CHECK)==-1):
        counter=counter+1
        if(counter%5 == 0):
            print("Loop counter = %d. Still installing..." %counter)
        time.sleep(0.5)
        r_apps = requests.get(url = LS_APP_URL+"deviceid="+deviceId, headers=getDevices_headers, verify=False)

    print("App "+APP_TO_CHECK+" successfully installed. EXIT.")
    end = time.time()
    elapsed_time = end - start
    print ("Time= "+str(elapsed_time))


if __name__ == "__main__":
    main()
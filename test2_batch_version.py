from sys import argv
import requests
import json
import time
import urllib3
import os
import subprocess as sp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# api-endpoint
MAN_ENDPOINT = "10.0.7.253:9443"
MW_ENDPOINT = "10.0.7.132:8083"
DEV_ENDPOINT = "192.168.101.23"

# V1 API
LOGIN_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/login/direct"
LS_DEV_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/devices"
LS_APP_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/devices/installed-apps?"
# GET_JOB_STATUS = "https://"+MAN_ENDPOINT+"/portal/api/v1/batches/:batchId"
GET_JOB_STATUS = "https://"+MAN_ENDPOINT+"/portal/api/v1/batches/"
BATCH_STATUS_READY = "https://"+MAN_ENDPOINT+"/portal/api/v1/batches/"

# DEV API
LIST_APP_DEV = "https://" + DEV_ENDPOINT + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"
LOGIN_DEV = "https://" + DEV_ENDPOINT + "/device/edge/api/v1/login/direct"

# Middleware API
DEPLOY_URL = "http://"+MW_ENDPOINT+"/deploy"


APP_TO_CHECK = "helloworld"
APP_VER = "0.0.1"
time_s = []
os.environ['EDGE_SKIP_TLS'] = '1'

def main():
    # check args
    if (len(argv)<3):
        print("usage -- python caller.py <iem_user> <iem_password>") #todo add docs
        return    
    API_NAME = argv[1]
    API_PWD = argv[2]
    API_NAME_MAN = argv[1]
    API_PWD_MAN = argv[3]

    # HEADERS and PAYLOADS (as Python dictionary)
    login_data = {'username':API_NAME,
        'password':API_PWD}
    login_data_man = {'username':API_NAME_MAN,
        'password':API_PWD_MAN}
    login_headers = {'content-type': 'application/json'}
    getDevices_headers = {'accept-language': 'en-US', 'authorization' : ''}
    get_Batch_headers = {'accept': 'application/json', 'authorization': ''}
    get_Batch_Ready_headers = {'authorization': ''}
    deploy_data = {'name' : APP_TO_CHECK, 'version' : APP_VER, 'platform' : 'siemens'}
    deploy_files = {'file' : open('./compose.yml','rb')}
    
    
    # POST login
    # API V1 r_login = requests.post(url = LOGIN_URL, data=json.dumps(login_data), headers=login_headers, verify=False)
    r_login = requests.post(url = LOGIN_DEV, data=json.dumps(login_data), headers=login_headers, verify=False)
    r_login_man = requests.post(url = LOGIN_URL, data=json.dumps(login_data_man), headers=login_headers, verify=False)

    # check return value
    if (r_login.status_code!=200):
        print("Something went wrong. Error code = "+str(r_login.status_code))
        return

    # extracting token
    api_access_token = r_login.json()["data"]["access_token"]
    api_access_token_man = r_login_man.json()["data"]["access_token"]
    print("\nThe token for device login is: %s\n" %str(api_access_token))
    print("\nThe token for management login is: %s\n" %str(api_access_token_man))
    getDevices_headers['authorization'] = api_access_token
    get_Batch_headers['authorization'] = api_access_token_man
    get_Batch_Ready_headers['authorization'] = api_access_token_man

    # NOTE for API DEV we skipped the GET devices call
        # GET devices (ASSUMPTION ONE --> I consider the first ([0]) device of the list)
        # --- 08efe36153fb4e559c3e8ffcbe9b6ccc ---
        #[0] position of the device 192.168.101.23
        # r_devices = requests.get(url = LS_DEV_URL, headers=getDevices_headers, verify=False)
        # deviceId = r_devices.json()["data"][0]["deviceId"]
        # print("\nThe deviceID is: %s\n" %deviceId)
    
    # GET installed apps on device
        # API V1
        # r_apps = requests.get(url = LS_APP_URL+"deviceid="+deviceId, headers=getDevices_headers, verify=False)

    r_apps = requests.get(url = LIST_APP_DEV, headers=getDevices_headers, verify=False)
    for a in r_apps.json()["data"]:
        if (a["title"]==APP_TO_CHECK): #app already installed
            print("App "+APP_TO_CHECK+" already installed. EXIT.") 
            return
    print("app is not here! --> START TIMER --> deploy")

    start = time.time()
    start_pending = time.time()
    r_deploy = requests.post(url = DEPLOY_URL, files = deploy_files, data=deploy_data, verify=False)
    print("RESPONSE -- ", r_deploy.json())
    print(r_deploy.json)    
    batch_id = r_deploy.json()["batch_id"]
    print("BATCH_ ID : ",batch_id)

    # V1 status check through batch_id
    # batch_id_response = os.system("iectl portal batches get-batch-jobs --batchId "+ batch_id)
    # while(batch_id_response == 1):
    #     time.sleep(0.1)
    #     batch_id_response = os.system("iectl portal batches get-batch-jobs --batchId "+ batch_id)
    # batch_id_response = json.loads(sp.getoutput("iectl portal batches get-batch-jobs --batchId "+ batch_id))
    # stat =  batch_id_response["data"][0]["status"]
    
    #comment: print("STATUS :", stat)
    # while (stat != 'PENDING'):
    #     batch_id_response = json.loads(sp.getoutput("iectl portal batches get-batch-jobs --batchId "+ batch_id))
    #     stat =  batch_id_response["data"][0]["status"]
    # # # ## STOP TIMER


    # ASSUMPTION: it is possible that the batch_id needs some time to be created on management
    # for this reason a check is added by adding time.sleep() each time the batch_id
    # is not found yet on the management
    # DEV API
    #NOTE batch_id comming has only 1 job in position [0] of data. If more than 1 jobs are linked check..
    r_status = requests.get(url = GET_JOB_STATUS + batch_id +"/jobs", headers=get_Batch_headers,verify=False) #getting the job status using the batch_id
    status =  r_status.json()["data"][0]["status"]

    while (status != 'EXECUTING'):
        r_status = requests.get(url = GET_JOB_STATUS + batch_id +"/jobs", headers=get_Batch_headers,verify=False) #getting the job status using the batch_id
        status =  r_status.json()["data"][0]["status"]
        print(status)
    end_pending = time.time()


    print(r_deploy.elapsed)
    if(r_deploy.status_code!=200):
        print("Something went wrong. Error code: "+r_deploy.status_code)
        return
   
    # V1 check installed app
    # ASSUMPTION TWO --> cannot find a "GET jobs" - I use the List Apps to check the installation
    # r_apps = requests.get(url = LS_APP_URL+"deviceid="+deviceId, headers=getDevices_headers, verify=False)
    # counter=0
    # while (r_apps.text.find(APP_TO_CHECK)==-1):
    #     counter=counter+1
    #     if(counter%5 == 0):
    #         print("Loop counter = %d. Still installing..." %counter)
    #     time.sleep(0.5)
    #     r_apps = requests.get(url = LS_APP_URL+"deviceid="+deviceId, headers=getDevices_headers, verify=False)

   # API DEV check installed app
    r_apps = requests.get(url = LIST_APP_DEV, headers=getDevices_headers, verify=False)
    counter=0
    while (r_apps.text.find(APP_TO_CHECK)==-1):
        counter=counter+1
        if(counter%5 == 0):
             print("Loop counter = %d. Still installing..." %counter)
        time.sleep(0.5)
        r_apps = requests.get(url = LIST_APP_DEV, headers=getDevices_headers, verify=False)

# calculating the times for total, pending status and excecuting status
    end = time.time()
    elapsed_time = end - start
    elapsed_time_pending = end_pending - start_pending
    elapsed_time_excecuted = elapsed_time - elapsed_time_pending

    print ("Time= ", str(elapsed_time), "PENDING TIME : ", elapsed_time_pending, " EXCECUTED TIME : ", elapsed_time_excecuted)
    for a in r_apps.json()["data"]:
        if (a["title"]==APP_TO_CHECK):
            print("The APP_ID is:" + a["applicationId"])  
            x = a["applicationId"]
    APP_ID= x
    print("Proceed to uninstall app with id : " + APP_ID + ". Are you sure? ..") 
    time.sleep(3)
    # uninstall app from device
    # python save command output to variable output = sp.getoutput(command)
    os.system("iectl portal batches submit-batch --appid " + APP_ID +" --infoMap " + '{"devices":[\"08efe36153fb4e559c3e8ffcbe9b6ccc\"]}' + " --operation uninstallApplication")
    # delete app from catalog
    os.system("iectl publisher edgemanagement application -a " + APP_ID + " deletecatalogapplication")
    time.sleep(60)
    
    
#for i in range(10): for stress test: is running the script 10 times
if __name__ == "__main__":
    main()
from email import header
from sys import argv
import sys
import requests
import json
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#----------------------------------------------------------------------------
# Endpoints
MAN_ENDPOINT = "10.0.7.253:9443"
MW_ENDPOINT = "10.0.7.132:8083"
PHY_DEV_ENDPOINT = "192.168.101.23"
VIR_DEV_ENDPOINT_1 = "10.0.7.249"
VIR_DEV_ENDPOINT_2 = "10.0.7.60"

# APIs
IED_LOGIN_URL_PHY = "https://"+PHY_DEV_ENDPOINT+"/device/edge/api/v1/login/direct"
IED_LOGIN_URL_VIR_1 = "https://"+VIR_DEV_ENDPOINT_1+"/device/edge/api/v1/login/direct"
IED_LOGIN_URL_VIR_2 = "https://"+VIR_DEV_ENDPOINT_2+"/device/edge/api/v1/login/direct"

IED_SYS_INFO_URL_PHY = "https://"+PHY_DEV_ENDPOINT+"/device/edge/b.service/api/v1/system-info"
IED_SYS_INFO_URL_VIR_1 = "https://"+VIR_DEV_ENDPOINT_1+"/device/edge/b.service/api/v1/system-info"

LIST_APP_DEV_VIR_1 = "https://" + VIR_DEV_ENDPOINT_1 + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"
LIST_APP_DEV_VIR_2 = "https://" + VIR_DEV_ENDPOINT_2 + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"
LIST_APP_DEV_PHY = "https://" + PHY_DEV_ENDPOINT + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"

APP_CTRL_DEV_VIR_1 = "https://" + VIR_DEV_ENDPOINT_1 + "/device/edge/b.service/api/v1/applications/"

IEM_LOGIN = "https://"+MAN_ENDPOINT+"/portal/api/v1/login/direct"
GET_JOB_STATUS = "https://"+MAN_ENDPOINT+"/portal/api/v1/batches/"

#IEM_INSTALL_ON_IED = "https://"+MAN_ENDPOINT+"/p.service/api/v4/applications/b490fab908b74244af564652dd4ff552/batch?operation=installApplication&allow=true"

DEPLOY_URL = "http://"+MW_ENDPOINT+"/deploy"

# Threshold
MAX_CPU_PERC = 30
MAX_MEM_PERC = 30

# Other Globals
APP_TO_CHECK = "stress"
APP_VER = "0.0.1"
IED_ID_PHY = "08efe36153fb4e559c3e8ffcbe9b6ccc"
IED_ID_VIR_1 = "6021b42db4bc4f6da8aca78a65e45dd2"
IED_ID_VIR_2 = "b3dd9c7cf7b347668624b66e04fd5592"
APP_NOT_INSTALLED = "app is not here!"

#----------------------------------------------------------------------------
# TODO 
    #   - Timing
    #   - Test all

def main():
    # check args
    if (len(argv)<4):
        print("usage -- python <prog_name> <ied_user> <ied_source_password> <ied_source_password>")
        return    
    IE_USERNAME = argv[1]
    IED_USERPWD_SRC = argv[2]
    IED_USERPWD_DEST = argv[3]

    # # POST login
    # ied_api_access_token = loginTo(IED_LOGIN_URL_VIR_1, IE_USERNAME, IED_USERPWD_SRC)

    # # GET Dev Info
    # mem_usage, cpu_usage = devInfo(IED_SYS_INFO_URL_VIR_1, ied_api_access_token)
    # print("\nThe perc of MEM used on device %s is: %s\n" %(str(PHY_DEV_ENDPOINT), str(mem_usage)))
    # print("\nThe perc of CPU used on device %s is: %s\n" %(str(PHY_DEV_ENDPOINT), str(cpu_usage)))

    # # CHECK Threshold
    # if (ied_mem_perc<MAX_CPU_PERC):
    #     print("No need for load balancing")
    #     return

    print("Trying to load balancing the device...")

    # # GET app ID - STOP app - UNINSTALL app
    # appID = checkAppInstalled(LIST_APP_DEV_VIR_1, APP_TO_CHECK, ied_api_access_token)
    # print ("The App ID of the %s app is %s\n" %(APP_TO_CHECK, appID))
    # if (appControl(APP_CTRL_DEV_VIR_1, ied_api_access_token, appID, "stop")):
    #     print("App %s successfully stopped" %(APP_TO_CHECK))
    # if (appControl(APP_CTRL_DEV_VIR_1, ied_api_access_token, appID, "uninstall")):
    #     print("App %s successfully uninstalled" %(APP_TO_CHECK))

    # DEPLOY
    deploy_files = {'file' : open('./compose.yml','rb')}
    deploy_data = {'name' : APP_TO_CHECK, 'version' : APP_VER, 'platform' : 'siemens'}
    res_mw_deploy = requests.post(url = DEPLOY_URL, files = deploy_files, data=deploy_data, verify=False)
    if (res_mw_deploy.status_code!=200):
        sys.exit("Something went wrong in the app installation. Error code = " + str(res_mw_deploy.status_code)+ "\nTEXT = " + str(res_mw_deploy.text))
    
    # CHECK INSTALLATION
    ied_api_access_token = loginTo(IED_LOGIN_URL_VIR_2, IE_USERNAME, IED_USERPWD_DEST)
    appID = APP_NOT_INSTALLED
    while(appID==APP_NOT_INSTALLED):
        print("installing...")
        time.sleep(2)
        appID = checkAppInstalled(LIST_APP_DEV_VIR_2, APP_TO_CHECK, ied_api_access_token)        
    print("app installed")

    sys.exit(0)

#----------------------------------------------------------------------------

def loginTo (url, username, pwd):
    """
    This func returns the login token (or ValueError in case of errors)
    """
    ied_login_data = {'username':username, 'password':pwd}
    login_header = {'content-type': 'application/json'}
    ied_res_login = requests.post(url = url, data=json.dumps(ied_login_data), headers=login_header, verify=False)
    if (ied_res_login.status_code!=200):
        raise ValueError("Something went wrong in the login api. Error code = "+str(ied_res_login.status_code))
    api_access_token = ied_res_login.json()["data"]["access_token"]
    print("\nThe login token is: %s\n" %str(api_access_token))
    return api_access_token


def checkAppInstalled (url, appName, access_token):
    """
    This func returns the app ID of the chosen app (if it is installed on dev)
    """
    app_list_header = {'accept-language': 'en-US', 'authorization' : access_token}
    r_list_apps = requests.get(url = url, headers=app_list_header, verify=False)
    if (r_list_apps.status_code!=200):
        raise ValueError("Something went wrong in the list app API. Error code = "+str(r_list_apps.status_code))
    for a in r_list_apps.json()["data"]:
        if (a["title"]==appName): #app installed
            return a["applicationId"]
    return APP_NOT_INSTALLED


def appControl (url, api_token, app_id, operation):
    """
    This function execute the requested operation on the app with ID app_id
    Operation = stat | stop | uninstall | restart
    """
    app_ctrl_header = {'Authorization' : ''}
    ied_res_app_stop = requests.post(url = APP_CTRL_DEV_VIR_1+app_id+"/"+operation, headers={'Authorization' : api_token}, verify=False)
    if (ied_res_app_stop.status_code!=200):
        raise ValueError("Something went wrong in the list app API. Error code = "+str(ied_res_app_stop.status_code))
    return True


def devInfo (url, api_token):
    ied_res_dev_info = requests.get(url = url, headers={'Authorization' : api_token}, verify=False)
    if (ied_res_dev_info.status_code!=200):
        raise ValueError("Something went wrong in the dev info api. Error code = "+str(ied_res_dev_info.status_code))
    ied_cpu_perc = ied_res_dev_info.json()["data"]["CpuPercentage"]
    ied_mem_perc = ied_res_dev_info.json()["data"]["MemoryPercentage"]
    return ied_cpu_perc, ied_mem_perc

#----------------------------------------------------------------------------

if __name__ == "__main__":
    main()

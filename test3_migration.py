from email import header
from sys import argv
import sys
import requests
import json

# Endpoints
MAN_ENDPOINT = "10.0.7.253:9443"
MW_ENDPOINT = "10.0.7.132:8083"
PHY_DEV_ENDPOINT = "192.168.101.23"
VIR_DEV_ENDPOINT_1 = "10.0.7.249"
VIR_DEV_ENDPOINT_2 = "10.0.7.60"

# APIs
IED_LOGIN_URL = "https://"+PHY_DEV_ENDPOINT+"/device/edge/api/v1/login/direct"
IED_LOGIN_URL_VIR_1 = "https://"+VIR_DEV_ENDPOINT_1+"/device/edge/api/v1/login/direct"

IED_SYS_INFO_URL = "https://"+PHY_DEV_ENDPOINT+"/device/edge/b.service/api/v1/system-info"

LIST_APP_DEV_VIR_1 = "https://" + VIR_DEV_ENDPOINT_1 + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"
LIST_APP_DEV_PHY = "https://" + PHY_DEV_ENDPOINT + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"

# Threshold
MAX_CPU_PERC = 30
MAX_MEM_PERC = 30

# Other Globals
APP_TO_CHECK = "stress"

def main():
    # check args
    if (len(argv)<3):
        print("usage -- python <prog_name> <ied_user> <ied_password>") #todo add docs
        return    
    IED_USERNAME = argv[1]
    IED_USERPWD = argv[2]

    # HEADERS and PAYLOADS (as Python dictionary)
    dev_info_header = {'Authorization' : ''}

    # POST login
    # ied_api_access_token = loginTo(IED_LOGIN_URL, IED_USERNAME,IED_USERPWD)
    ied_api_access_token = loginTo(IED_LOGIN_URL_VIR_1, IED_USERNAME,IED_USERPWD)

    # GET Dev Info
    # dev_info_header['Authorization'] = ied_api_access_token
    # ied_res_dev_info = requests.get(url = IED_SYS_INFO_URL, headers=dev_info_header, verify=False)
    # if (ied_res_dev_info.status_code!=200):
    #     print("Something went wrong in the device info api. Error code = "+str(ied_res_dev_info.status_code))
    #     return
    # ied_cpu_perc = ied_res_dev_info.json()["data"]["CpuPercentage"]
    # ied_mem_perc = ied_res_dev_info.json()["data"]["MemoryPercentage"]

    # print("\nThe perc of MEM used on device %s is: %s\n" %(str(PHY_DEV_ENDPOINT), str(ied_mem_perc)))
    # print("\nThe perc of CPU used on device %s is: %s\n" %(str(PHY_DEV_ENDPOINT), str(ied_cpu_perc)))

    # if (ied_mem_perc<MAX_CPU_PERC):
    #     print("No need for load balancing")
    #     return

    print("Trying to load balancing the device...")

    appID = checkAppInstalled(LIST_APP_DEV_VIR_1, APP_TO_CHECK, ied_api_access_token)
    print ("The App ID of the %s app is %s.\n" %(APP_TO_CHECK, appID))
    #TODO APP LIST - GET APP ID - STOP&UNINSTALL

    #TODO LOGIN TO SECOND DEVICE - DEPLOY APP
    
    return


def loginTo (url, username, pwd):
    """
    This func returns the login token
    """
    ied_login_data = {'username':username, 'password':pwd}
    login_header = {'content-type': 'application/json'}
    ied_res_login = requests.post(url = url, data=json.dumps(ied_login_data), headers=login_header, verify=False)
    if (ied_res_login.status_code!=200):
        # print("Something went wrong in the login api. Error code = "+str(ied_res_login.status_code))
        # return
        raise ValueError("Something went wrong in the login api. Error code = "+str(ied_res_login.status_code))
    api_access_token = ied_res_login.json()["data"]["access_token"]
    print("\nThe login token is: %s\n" %str(api_access_token))
    return api_access_token


def checkAppInstalled (url, appName, access_token):
    """
    This func returns the app ID of the chosen app
    """
    app_list_header = {'accept-language': 'en-US', 'authorization' : access_token}
    r_list_apps = requests.get(url = url, headers=app_list_header, verify=False)
    if (r_list_apps.status_code!=200):
        raise ValueError("Something went wrong in the list app API. Error code = "+str(r_list_apps.status_code))
    for a in r_list_apps.json()["data"]:
        if (a["title"]==appName): #app installed
            return a["applicationId"]
    return "app is not here!"


if __name__ == "__main__":
    main()

from email import header
from sys import argv
import sys
import requests
import json

# Endpoints
MAN_ENDPOINT = "10.0.7.253:9443"
MW_ENDPOINT = "10.0.7.132:8083"
PHY_DEV_ENDPOINT = "192.168.101.23"
VIR_DEV_ENDPOINT_1 = "10.0.7.60"
PHY_DEV_ENDPOINT_2 = "10.0.7.249"

# APIs
IED_LOGIN_URL = "https://"+PHY_DEV_ENDPOINT+"/device/edge/api/v1/login/direct"
IED_SYS_INFO_URL = "https://"+PHY_DEV_ENDPOINT+"/device/edge/b.service/api/v1/system-info"

def main():
    # check args
    if (len(argv)<3):
        print("usage -- python <prog_name> <ied_user> <ied_password>") #todo add docs
        return    
    IED_USERNAME = argv[1]
    IED_USERPWD = argv[2]

    # HEADERS and PAYLOADS (as Python dictionary)
    ied_login_data = {'username':IED_USERNAME, 'password':IED_USERPWD}
    login_header = {'content-type': 'application/json'}
    dev_info_header = {'Authorization' : ''}

    # POST login
    ied_res_login = requests.post(url = IED_LOGIN_URL, data=json.dumps(ied_login_data), headers=login_header, verify=False)
    if (ied_res_login.status_code!=200):
        print("Something went wrong in the login api. Error code = "+str(ied_res_login.status_code))
        return
    ied_api_access_token = ied_res_login.json()["data"]["access_token"]
    print("\nThe login token for the device is: %s\n" %str(ied_api_access_token))

    # GET Dev Info
    dev_info_header['Authorization'] = ied_api_access_token
    ied_res_dev_info = requests.get(url = IED_SYS_INFO_URL, headers=dev_info_header, verify=False)
    if (ied_res_dev_info.status_code!=200):
        print("Something went wrong in the device info api. Error code = "+str(ied_res_dev_info.status_code))
        return
    ied_cpu_perc = ied_res_dev_info.json()["data"]["CpuPercentage"]
    ied_mem_perc = ied_res_dev_info.json()["data"]["MemoryPercentage"]

    print("\nThe perc of MEM used on device %s is: %s\n" %(str(PHY_DEV_ENDPOINT), str(ied_mem_perc)))
    print("\nThe perc of CPU used on device %s is: %s\n" %(str(PHY_DEV_ENDPOINT), str(ied_cpu_perc)))

    return


if __name__ == "__main__":
    main()

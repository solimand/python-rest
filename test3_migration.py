from email import header
from sys import argv
import sys , getopt
import requests
import json
import time
import urllib3
import logging
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#@----------------------------------------------@
# TODO                                          #
#                                               #
#   - Fix the deadlock in devInfo function      #
#                                               #
#@----------------------------------------------@

# Endpoints & IDs
MAN_ENDPOINT = "10.0.7.253:9443"
MW_ENDPOINT = "10.0.7.132:8083"
PHY_DEV_ENDPOINT = "192.168.101.23"
VIR_DEV_ENDPOINT_1 = "10.0.7.249"
VIR_DEV_ENDPOINT_2 = "10.0.7.60"
# IED_ID_PHY = "08efe36153fb4e559c3e8ffcbe9b6ccc"
# IED_ID_VIR_1 = "6021b42db4bc4f6da8aca78a65e45dd2"
# IED_ID_VIR_2 = "b3dd9c7cf7b347668624b66e04fd5592"

# APIs
IED_LOGIN_URL_PHY = "https://"+PHY_DEV_ENDPOINT+"/device/edge/api/v1/login/direct"
IED_LOGIN_URL_VIR_1 = "https://"+VIR_DEV_ENDPOINT_1+"/device/edge/api/v1/login/direct"
IED_LOGIN_URL_VIR_2 = "https://"+VIR_DEV_ENDPOINT_2+"/device/edge/api/v1/login/direct"
# IEM_LOGIN_URL = "https://"+MAN_ENDPOINT+"/portal/api/v1/login/direct"

IED_SYS_INFO_URL_PHY = "https://"+PHY_DEV_ENDPOINT+"/device/edge/b.service/api/v1/system-info"
IED_SYS_INFO_URL_VIR_1 = "https://"+VIR_DEV_ENDPOINT_1+"/device/edge/b.service/api/v1/system-info"

LIST_APP_DEV_VIR_1 = "https://" + VIR_DEV_ENDPOINT_1 + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"
LIST_APP_DEV_VIR_2 = "https://" + VIR_DEV_ENDPOINT_2 + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"
LIST_APP_DEV_PHY = "https://" + PHY_DEV_ENDPOINT + "/device/edge/b.service/api/v1/applications/search/pages/1?pageSize=100"

APP_CTRL_DEV_VIR_1 = "https://" + VIR_DEV_ENDPOINT_1 + "/device/edge/b.service/api/v1/applications/"
APP_CTRL_DEV_VIR_2 = "https://" + VIR_DEV_ENDPOINT_2 + "/device/edge/b.service/api/v1/applications/"
APP_CTRL_DEV_PHY = "https://" + PHY_DEV_ENDPOINT + "/device/edge/b.service/api/v1/applications/"

# GET_JOB_STATUS = "https://"+MAN_ENDPOINT+"/portal/api/v1/batches/"
# IEM_INSTALL_ON_IED = "https://"+MAN_ENDPOINT+"/p.service/api/v4/applications/b490fab908b74244af564652dd4ff552/batch?operation=installApplication&allow=true"
# IEM_INSTALL_ON_IED = "https://"+MAN_ENDPOINT+"/portal/api/v1/batches?operation=installApplication&appid=b490fab908b74244af564652dd4ff552"
#DEPLOY_URL = "http://"+MW_ENDPOINT+"/deploy"

DEPLOY_ON_URL = "http://"+MW_ENDPOINT+"/deployOn"

# Threshold
MAX_CPU_PERC = 10
MAX_MEM_PERC = 30

# Other Globals
APP_TO_CHECK = "stress"
APP_VER = "0.0.1"
APP_NOT_INSTALLED = "app is not here!"
DEVICE_PHY = 1
DEVICE_VIR1 = 2
DEVICE_VIR2 = 3
DIRECTIONS_STRING = "VV (from virtual to virtual) - PV (from physical to virtual) - VP (from vritual to physical)"
USAGE = """usage -- python <prog_name> -d <direction> <ied_user> <ied_source_pwd> <ied_dest_pwd>
        Allowed directions = \n\t\t"""+DIRECTIONS_STRING
DEBUG_LOG_FILE_NAME="migration.log"
DEBUG_LOG_PATH="./out/"
DEBUG_LOG_COMPLETE_PATH = DEBUG_LOG_PATH+DEBUG_LOG_FILE_NAME

# EXEC constants
LOGIN_SOURCE_URL, LOGIN_DEST_URL = "", ""
LIST_APP_SOURCE_URL, LIST_APP_DEST_URL = "", ""
DEV_SOURCE, DEV_DEST, DEV_SOURCE_INFO_URL = "", "", ""
APP_CTRL_SOURCE_URL, APP_CTRL_DEST_URL = "", ""


def main(argv):

    #ARGS CHECK
    try:
        opts, args = getopt.getopt(argv,"hd:",["direction="])
    except getopt.GetoptError:
        print ("Options parsing exception.\n"+USAGE)
        sys.exit(2)
    if(len(args))<3:
        print ("Argument parsing exception.\n"+USAGE)
        sys.exit(3)

    for opt, arg in opts:
        if opt == '-h':
            print(USAGE)
            sys.exit(0)
        elif (opt in ("-d", "--direction")):
            direction = arg
            if (direction not in ("VV", "PV", "VP")):
                print ("Direction Wrong.\n"+USAGE)
                sys.exit(3)
    IE_USERNAME = args[0]
    IED_PWD_SRC = args[1]
    IED_PWD_DEST = args[2]

    # LOGGING and INIT
    print("Starting test with migration mode: "+direction)
    Path("./out").mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('MigrationTest')
    logger.setLevel(logging.DEBUG)
    log_fh = logging.FileHandler(DEBUG_LOG_COMPLETE_PATH)
    log_fh.setLevel(logging.DEBUG)
    logger.addHandler(log_fh)
    #logger.debug("Starting test with migration mode: "+direction)
    initConstants(direction)
    
    # POST login
    ied_api_access_token = loginTo(LOGIN_SOURCE_URL, IE_USERNAME, IED_PWD_SRC)

    # INSTALL  app on first device (if not installed) - LOOP until installed
    if (checkAppInstalled(LIST_APP_SOURCE_URL, APP_TO_CHECK, ied_api_access_token) == APP_NOT_INSTALLED):
        appDeploy(DEPLOY_ON_URL, './compose.yml', APP_TO_CHECK, APP_VER, DEV_SOURCE)
    appID = checkAppInstalled(LIST_APP_SOURCE_URL, APP_TO_CHECK, ied_api_access_token)
    while(appID==APP_NOT_INSTALLED):
        print("installing...")
        time.sleep(5)
        appID = checkAppInstalled(LIST_APP_SOURCE_URL, APP_TO_CHECK, ied_api_access_token)
    print("App Installed on first device")

    # GET Dev Info - Loop till threshold
    while True:
        print("Checking Device Status...")
        mem_usage, cpu_usage = devInfo(DEV_SOURCE_INFO_URL, ied_api_access_token)
        print("\nThe perc of MEM used on device source is: %s\n" %(str(mem_usage)))
        print("\nThe perc of CPU used on device source is: %s\n" %(str(cpu_usage)))
        logger.debug("From "+direction[0]+ " to --> "+direction[1]+": MEM used = %s; CPU used = %s" %(str(mem_usage), str(cpu_usage)))
        if (float(cpu_usage)>MAX_CPU_PERC):
            break

    print("Trying to load balancing the device...")

    migr_start_time = time.time()

    # GET app ID - UNINSTALL app from source device
    appID = checkAppInstalled(LIST_APP_SOURCE_URL, APP_TO_CHECK, ied_api_access_token)
    print ("The App ID of the %s app is %s\n" %(APP_TO_CHECK, appID))
    if (appControl(APP_CTRL_SOURCE_URL, ied_api_access_token, appID, "uninstall")):
        print("App %s successfully uninstalled from first device\n" %(APP_TO_CHECK))

    # DEPLOY on destination device
    appDeploy(DEPLOY_ON_URL, './compose.yml', APP_TO_CHECK, APP_VER, DEV_DEST)
    print("Installing app %s on second device...\n" %(APP_TO_CHECK))

    # CHECK INSTALLATION on destination device
    ied_api_access_token = loginTo(LOGIN_DEST_URL, IE_USERNAME, IED_PWD_DEST)
    appID = checkAppInstalled(LIST_APP_DEST_URL, APP_TO_CHECK, ied_api_access_token)
    while(appID==APP_NOT_INSTALLED):
        print("installing...")
        time.sleep(2)
        appID = checkAppInstalled(LIST_APP_DEST_URL, APP_TO_CHECK, ied_api_access_token)
    
    migr_end_time = time.time()
    migr_time = migr_end_time-migr_start_time
    print("App migrated on second device, cluster balanced, time exec = " + str(migr_time))
    logger.debug(migr_time)
    time.sleep(20)

    # UNINSTALL app from the destination for further runs
    print("\nUninstalling app from second device for further runs...\n")
    if (appControl(APP_CTRL_DEST_URL, ied_api_access_token, appID, "uninstall")):
        print("App %s successfully uninstalled from second device\n" %(APP_TO_CHECK))
    time.sleep(20)

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
    ied_res_app_stop = requests.post(url = url+app_id+"/"+operation, headers={'Authorization' : api_token}, verify=False)
    if (ied_res_app_stop.status_code!=200):
        raise ValueError("Something went wrong in the " + operation + " app API. Error code = "+str(ied_res_app_stop.status_code))
    return True


def devInfo (url, api_token):
    ied_res_dev_info = requests.get(url = url, headers={'Authorization' : api_token}, verify=False)
    if (ied_res_dev_info.status_code!=200):
        if(ied_res_dev_info.status_code==500): ## something went wrong, repeat the request
            print("Error Code %d Retrying to check device status..." %(ied_res_dev_info.status_code))
            time.sleep(2) # slow down the subsequent call
            return devInfo(url, api_token)
        raise ValueError("Something went wrong in the dev info api. Error code = "+str(ied_res_dev_info.status_code))
    ied_cpu_perc = ied_res_dev_info.json()["data"]["CpuPercentage"]
    ied_mem_perc = ied_res_dev_info.json()["data"]["MemoryPercentage"]
    return ied_cpu_perc, ied_mem_perc


def appDeploy(url, file, appToCheck, appVer, device=None):
    deploy_files = {'file' : open(file,'rb')}
    deploy_data = {'name' : appToCheck, 'version' : appVer, 'platform' : 'siemens'}
    if (device!=None):
        deploy_data["device"]=device
    res_mw_deploy = requests.post(url = url, files = deploy_files, data=deploy_data, verify=False)
    if (res_mw_deploy.status_code!=200):
        raise ValueError("Something went wrong in the app installation. Error code = " + str(res_mw_deploy.status_code)+ "\nTEXT = " + str(res_mw_deploy.text))    
    return


def initConstants(direction):
    global LOGIN_SOURCE_URL, LOGIN_DEST_URL, LIST_APP_SOURCE_URL, LIST_APP_DEST_URL
    global DEV_SOURCE, DEV_DEST, DEV_SOURCE_INFO_URL, APP_CTRL_SOURCE_URL, APP_CTRL_DEST_URL
    if(direction == "VV"):
        LOGIN_SOURCE_URL=IED_LOGIN_URL_VIR_1
        LOGIN_DEST_URL=IED_LOGIN_URL_VIR_2
        LIST_APP_SOURCE_URL=LIST_APP_DEV_VIR_1
        LIST_APP_DEST_URL=LIST_APP_DEV_VIR_2
        DEV_SOURCE=DEVICE_VIR1
        DEV_DEST=DEVICE_VIR2
        DEV_SOURCE_INFO_URL=IED_SYS_INFO_URL_VIR_1
        APP_CTRL_SOURCE_URL=APP_CTRL_DEV_VIR_1
        APP_CTRL_DEST_URL=APP_CTRL_DEV_VIR_2
    elif (direction == "PV"):
        LOGIN_SOURCE_URL=IED_LOGIN_URL_PHY
        LOGIN_DEST_URL=IED_LOGIN_URL_VIR_1
        LIST_APP_SOURCE_URL=LIST_APP_DEV_PHY
        LIST_APP_DEST_URL=LIST_APP_DEV_VIR_1
        DEV_SOURCE=DEVICE_PHY
        DEV_DEST=DEVICE_VIR1
        DEV_SOURCE_INFO_URL=IED_SYS_INFO_URL_PHY
        APP_CTRL_SOURCE_URL=APP_CTRL_DEV_PHY
        APP_CTRL_DEST_URL=APP_CTRL_DEV_VIR_1
    elif (direction == "VP"):
        LOGIN_SOURCE_URL=IED_LOGIN_URL_VIR_1
        LOGIN_DEST_URL=IED_LOGIN_URL_PHY
        LIST_APP_SOURCE_URL=LIST_APP_DEV_VIR_1
        LIST_APP_DEST_URL=LIST_APP_DEV_PHY
        DEV_SOURCE=DEVICE_VIR1
        DEV_DEST=DEVICE_PHY
        DEV_SOURCE_INFO_URL=IED_SYS_INFO_URL_VIR_1
        APP_CTRL_SOURCE_URL=APP_CTRL_DEV_VIR_1
        APP_CTRL_DEST_URL=APP_CTRL_DEV_PHY

#----------------------------------------------------------------------------

if __name__ == "__main__":
    main(sys.argv[1:])

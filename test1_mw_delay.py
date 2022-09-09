import os
from multiprocessing import Process
import time

# 1 prepare your compose.yml
# 2 set compose yml path in the request on postman
# 3 export the collection (JSON)
# 4 set the path of the collection in the following variable
collection = "C:/Users/it164/OneDrive/Desktop/brex/DeepMon-MW-test-sharing.postman_collection.json"
# command = "newman run "+ collection 
command = "newman run "+ collection + " -r csv --reporter-csv-includeBody --reporter-csv-export ./csv/csv-"+ str(time.time()).replace('.','')+".csv"

def run_requests():
    os.system(command)

if __name__ == "__main__":
    for f in range(20):  # number of the tries     
        p1 = Process(target = run_requests)
        p1.start()        
        p1.join(5) # seconds of delay between subsequent requests


# python-rest
Simply python REST API call using ```requests``` module.
This is a pool of tests running against a custom Middleware service and a Siemens Industrial Edge deployment.

# Requirements
- python 3,
- module ```request```.

# TEST Description
We provided a set of tests with different purposes.

## TEST 1 - Middleware Delay
We run our collection in async way, with different delays between async requests.

## TEST 2 - Downtime
We let an application to crash, detect the crash, and re-install the application on the device.

## TEST 3 - Load Balancing and Migration 
we set a threshold and monitored the violations. If an application on device X uses too many resources, we move it on device Y.
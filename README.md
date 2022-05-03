# python-rest
Simply python REST API call using ```request``` module

# Requirements
- python 3
- module ```request```

# Deployment
Chain call:
- POST[user, password] = TOKEN
- GET_LIST_DEVICES[TOKEN] = DEV_ID
- GET_INSTALLED_APP[TOKEN, DEV_ID] = find if app 'helloworld' is installed

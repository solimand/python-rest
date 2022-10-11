#!/bin/sh

echo "Starting OPC UA Connector deployment..."

curl --write-out "%{http_code}\n" --request POST 'http://10.0.7.132:8083/deploy' \
    --form 'name="opc-conn"' \
    --form 'version="0.0.1"' \
    --form 'file=@"./edgex-opc-connContainer/compose.yml"' \
    --form 'platform="edgex"'


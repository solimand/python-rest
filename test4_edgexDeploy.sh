#!/bin/sh

for i in {1..24}
do 
    echo "Starting OPC UA Connector deployment..."

    start_millis=$(date +%s%N | cut -b1-13)

    curl --write-out "%{http_code}\n\t" --request POST 'http://10.0.7.132:8083/deploy' \
        --form 'name="opc-conn"' \
        --form 'version="0.0.1"' \
        --form 'file=@"./edgex-opc-connContainer/compose.yml"' \
        --form 'platform="edgex"'

    end_millis=$(date +%s%N | cut -b1-13)

    echo "Time elapsed "
    echo "scale=3; $(($end_millis-$start_millis))/1000" | bc -l

    # I will delete the remote container for subsequent runs
    # You need an allowed key to connect to remote host
    ssh ubuntu@10.0.7.120 'docker rm $(docker stop device-opcua)'
    echo "... container removed!"
done
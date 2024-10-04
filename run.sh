#!/bin/bash

# Check if at least 3 arguments are passed
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 network_port server_port client_port"
    exit 1
fi

# Assigning passed arguments to variables for better readability
network_port="$1"
server_port="$2"
client_port="$3"
addr="127.0.0.1"
buff=8000
working_dir="/Users/philliple/Documents/Networks/lab2-philluple" # Add your working directory here

osascript -e "tell app \"Terminal\"
    do script \"cd $working_dir; echo Starting the network on port $network_port...; python network.py $network_port $addr $client_port $addr $server_port Loss.txt\"
end tell"

osascript -e "tell app \"Terminal\"
    do script \"cd $working_dir; echo Starting server on port $server_port...; python app_server.py $server_port $buff\"
end tell"

osascript -e "tell app \"Terminal\"
    do script \"cd $working_dir; echo Starting client on port $client_port...; python app_client.py $client_port $addr $network_port 1024\"
end tell"
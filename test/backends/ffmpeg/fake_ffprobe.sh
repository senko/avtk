#!/bin/bash

if [ "$6" == "error" ]; then
    echo "This is a fake error"
    exit -1
fi

echo "{\"status\": \"ok\"}"
exit 0

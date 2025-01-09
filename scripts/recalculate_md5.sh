#!/bin/bash

# Check if the right number of arguments is passed
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <transfer_list> <output>"
    exit 1
fi

# Define paths
transfer_list=$1
output=$2

awk '
BEGIN { 
    FS="\t" 
} 
$6 == "MISMATCH" { 
    cmd = "ichksum " $3
    cmd | getline result
    close(cmd)
    
    split(result, arr)
    
    if (arr[2] == $5) 
        status = "MATCH"
    else 
        status = "MISMATCH"
    
    print $1, $2, $3, $4, arr[2], status
} 
' $transfer_list > $output

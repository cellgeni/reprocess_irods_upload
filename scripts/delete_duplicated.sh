#!/bin/bash

# Define paths
filelist="/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/duplicated.txt"

# Read each directory from the list and move it
while IFS= read -r dir; do
    # Check if the directory exists in the source and not already in the target
    if [ -d "$dir" ]; then
        rm -rf $dir
        echo "Deleted: $dir"
    else
        echo "Directory not found : $dir"
    fi
done < "$filelist"
#!/bin/bash

# Check if the right number of arguments is passed
if [[ -z "$1" ]]; then
    echo "Usage: $0 <good_datasets_list>"
    exit 1
fi

# Define paths
good_dirs_list=$1
target_dir="/lustre/scratch127/cellgen/cellgeni/reprocessing-datasets-project/irods"

# Create the target directory if it doesn't exist
mkdir -p "$target_dir"

# Read each directory from the list and move it
while IFS= read -r subdir; do
    # Construct the full source path and target path
    full_path="$source_dir/$subdir"
    target_path="$target_dir/$subdir"
    
    # Check if the directory exists in the source and not already in the target
    if [ -d "$full_path" ]; then
        if [ ! -d "$target_path" ]; then
            mv "$full_path" "$target_dir"
            echo "Moved: $subdir"
        else
            echo "Directory already exists in target: $subdir"
            echo "$full_path" >> duplicated.txt
        fi
    else
        echo "Directory not found in source: $subdir"
    fi
done < "$good_dirs_list"

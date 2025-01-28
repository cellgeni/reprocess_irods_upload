#!/bin/bash

# Check if the right number of arguments is passed
if [[ -z "$1" ]]; then
    echo "Usage: $0 <good_datasets_list>"
    exit 1
fi

# Define paths
good_dirs_list=$1
target_dir="/lustre/scratch127/cellgen/cellgeni/reprocessing-datasets-project/irods"

# Add newline at the end if needed
sed -i -e '$a\' $good_dirs_list

# Create the target directory if it doesn't exist
mkdir -p "$target_dir"

# Read each directory from the list and move it
while IFS= read -r dataset_path; do
    # Construct the full source path and target path
    dataset=$(basename $dataset_path)
    target_path="$target_dir/$dataset"
    
    # Check if the directory exists in the source and not already in the target
    if [ -d "$dataset_path" ]; then
        if [ ! -d "$target_path" ]; then
            mv "$dataset_path" "$target_dir"
            echo "Moved: $dataset"
        else
            echo "Directory already exists in target: $dataset"
            echo "$dataset_path" >> duplicated.txt
        fi
    else
        echo "Directory not found in source: $dataset"
    fi
done < "$good_dirs_list"

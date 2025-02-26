#!/bin/bash

# Define the base directory for good datasets
base_dir="/lustre/scratch127/cellgen/cellgeni/reprocessing-datasets-project/irods"

# Iterate through all subdirectories in the base directory
for dir in "$base_dir"/*/; do
    # Check if 'fastqs' directory exists and delete it
    if [ -d "$dir/fastqs" ]; then
        rm -rf "$dir/fastqs"
        echo "Deleted: $dir/fastqs"
    fi

    # Check if 'done_wget' directory exists and delete it
    if [ -d "$dir/done_wget" ]; then
        rm -rf "$dir/done_wget"
        echo "Deleted: $dir/done_wget"
    fi
done

# Delete logs and other txt files
find $base_dir -wholename '*wget-log' -exec rm -f {} +
find $base_dir -type f -wholename '*.sh' -exec rm -f {} +
find $base_dir -type f -wholename '*.pl' -exec rm -f {} +
find $base_dir -type f -wholename '*.bsub.*' -exec rm -f {} +

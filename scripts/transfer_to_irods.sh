#!/bin/bash

# Exit on errors
set -e

# Ensure correct number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_directory> <irods_target_directory>"
    exit 1
fi

# Input arguments and remove trailing slash if it exists
SOURCE_DIR="${1%/}"
IRODS_TARGET_DIR="${2%/}"

# Get dataset name
dataset=$(basename $SOURCE_DIR)

# Generate a list of files to load
FILELIST="${dataset}.file.list"
find "$SOURCE_DIR" -type f > $FILELIST

# Generate output tracking file
TRACKING_FILE="${dataset}_tracking.txt"
if [[ -f $TRACKING_FILE ]]; then
    echo "$TRACKING_FILE exists. Continuing loading..."
else
    echo -e "dataset\tfilepath\tirodspath\tmd5" > "$TRACKING_FILE"
fi

# Find all files in the source directory and process
while IFS= read -r file
do
    if ! grep -qP "\t$file\t" "$TRACKING_FILE"; then
        # Extract relative path and directory name
        relative_path="${file#$SOURCE_DIR/}"

        # Build iRODS target path
        irods_path="${IRODS_TARGET_DIR}/${dataset}/${relative_path}"

        # Calculate MD5 checksum
        md5=$(md5sum "$file" | awk '{print $1}')

        # Load file to the IRODS
        irods_dir=$(dirname "$irods_path")
        imkdir -p "$irods_dir"
        iput -K -N 0 -f -X $dataset.restart.txt --retries 5 --metadata="series;${dataset};;md5;${md5};;" "$file" "$irods_path" > /dev/null

        # Write details to tracking file
        echo -e "$dataset\t$file\t$irods_path\t$md5" >> "$TRACKING_FILE"
    fi
done < "$FILELIST"

echo "COMPLETED"
rm "$FILELIST"

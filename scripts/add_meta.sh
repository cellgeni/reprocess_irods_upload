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

# Get dataset name and add it to meta
dataset=$(basename $IRODS_TARGET_DIR)
echo "Adding metadata to iRODS collection: $IRODS_TARGET_DIR"
imeta set -C "$IRODS_TARGET_DIR" "accession number" "$dataset"

# Iterate over all files matching the pattern 'sample.tsv'
for file in "$SOURCE_DIR"/*.tsv; do
    # Skip if no matching files exist
    [[ -e "$file" ]] || continue

    # Extract the dataset name (remove directory and extension)
    sample_accession_number=$(basename "$file" .tsv)

    # Define the corresponding iRODS collection
    irods_collection="$IRODS_TARGET_DIR/$sample_accession_number"

    # Add basic metadata
    echo "Adding metadata to iRODS collection: $irods_collection"
    imeta set -C "$irods_collection" "accession number" "$dataset"
    imeta set -C "$irods_collection" "sample_accession_number number" "$sample_accession_number"

    # Read each line from the file
    while IFS=$'\t' read -r key value; do
        # Skip empty lines or invalid rows
        [[ -z "$key" || -z "$value" ]] && continue

        # List metadata for the collection
        metadata=$(imeta ls -C "$irods_collection")
        # Check if key and value are in metadata
        if echo "$metadata" | grep -qzP "attribute: $key\nvalue: $value"; then
            echo "AVU $key:$value are already in $irods_collection"
            continue
        else
            # Add metadata to the iRODS collection
            if [[ "$key" == "experiment" || "$key" == "run" ]]; then
                imeta add -C "$irods_collection" "$key" "$value"
            else
                imeta set -C "$irods_collection" "$key" "$value"
            fi
        fi
    done < "$file"

    echo "Metadata for $irods_collection added successfully."
done

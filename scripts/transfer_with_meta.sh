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

# Set script PATHS
get_meta_script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/scripts/get_metadata.py
transfer_script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/scripts/transfer_to_irods.sh
add_meta_script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/scripts/add_meta.sh

# Set output dir
outputdir=metadata
dataset=$(basename "$SOURCE_DIR")

# Get metadata
echo "Step1. Getting metadata ..."
$get_meta_script --outputdir "${outputdir}" $SOURCE_DIR 

# Load Dataset to IRODS
echo "Step2. Loading data to $IRODS_TARGET_DIR/$dataset on IRODS..."
$transfer_script "$SOURCE_DIR" "$IRODS_TARGET_DIR"

# Add metadata
echo "Step3. Adding metadata..."
$add_meta_script "${outputdir}" "${IRODS_TARGET_DIR}/${dataset}"

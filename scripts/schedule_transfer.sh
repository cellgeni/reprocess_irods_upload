#!/bin/bash

# Ensure correct number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <datasetlist> <transfer>"
    exit 1
fi

target=/archive/cellgeni/datasets
dataset_list=$1

workdir=$2
bsub_script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/scripts/transfer_with_meta.bsub

# Get the number of datasets to transfer
NUM=$(wc -l <"$dataset_list")

# Check if there are any datasets to transfer
if [ "$NUM" -eq 0 ]; then
    echo "No datasets to process."
    exit 0
fi

cd $workdir
bsub -env "all, ENV_DATASET_LIST=$dataset_list, TARGET=$target, ENV_WORKDIR=$workdir" -J "transfer_to_irods[1-${NUM}]%7" <$bsub_script

#!/bin/bash

# Ensure correct number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <datasetlist> <transfer>"
    exit 1
fi


target=/archive/cellgeni/datasets
dataset_list=$1

workdir=$2
bsub_script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/scripts/transfer_with_meta.bsub 

while read -r source
do
    dataset=$(basename $source)
    mkdir -p "${workdir}/${dataset}"
    cd "${workdir}/${dataset}"
    cp $bsub_script .
    bsub -env "all, SOURCE=$source, TARGET=$target" -J "reprocess_to_irods.$dataset" < transfer_with_meta.bsub
done < "$dataset_list"
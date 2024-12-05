#!/bin/bash

target=/archive/cellgeni/datasets
dataset_list=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/to_load_list0.txt

workdir=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/transfer
bsub_script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/scripts/transfer_with_meta.bsub 

while read -r source
do
    dataset=$(basename $source)
    mkdir -p "${workdir}/${dataset}"
    cd "${workdir}/${dataset}"
    cp $bsub_script .
    bsub -env "all, SOURCE=$source, TARGET=$target" -J "reprocess_to_irods.$dataset" < transfer_with_meta.bsub
done < "$dataset_list"
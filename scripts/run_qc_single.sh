#!/bin/bash

qc_script_path=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/reprocess_public_10x/scripts/solo_QC.sh

basedir=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/reprocessing-datasets-project/
dataset=$1

cd $basedir

if [[ -d "${basedir}/${dataset}" ]]
then
    cd "${basedir}/${dataset}"
    if [[ ! -s "${dataset}.solo_qc.tsv" ]]
    then
        cp $qc_script_path ./solo_QC.sh
        ./solo_QC.sh > "${dataset}.solo_qc.tsv"
    fi
fi

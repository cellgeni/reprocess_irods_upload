#!/bin/bash

qc_script_path=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/reprocess_public_10x/scripts/solo_QC.sh

basedir=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/reprocessing-datasets-project/

cd $basedir
for dataset in $( echo E-MTAB* GSE*  PRJNA* SDY* )
do
    if [[ -d "${basedir}/${dataset}" ]]
    then
        cd "${basedir}/${dataset}"
        if [[ ! -f "${dataset}.solo_qc.tsv" ]]
        then
            cp $qc_script_path ./solo_QC.sh
            ./solo_QC.sh > "${dataset}.solo_qc.tsv"
        fi
    fi
done

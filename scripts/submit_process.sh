#!/bin/bash -e


# Ensure correct number of arguments
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <metadata_directory> <irods_target_directory>"
  exit 1
fi

INPUT_FILE=$1
SCRIPT=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/scripts/reprocess.bsub
: > finished.tsv

while IFS=$'\t' read -r DATASET SPECIE NUM_ALL NUM_10X SAMPLES
do  
    echo $SAMPLES | tr ',' '\n' > "${DATASET}_subset.txt"
    bsub -env "all, DATASET=$DATASET, SUBSET=${DATASET}_subset.txt" < $SCRIPT
done < "$INPUT_FILE"

#!/bin/bash -e


# Ensure correct number of arguments
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <list_of_datasets>"
  exit 1
fi

INPUT_FILE=$1
SCRIPT=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/scripts/reprocess.bsub
: > finished.tsv

while IFS=$'\t' read -r DATASET SPECIE NUM_ALL NUM_10X SAMPLES
do
  # write subset list to file
  echo $SAMPLES | tr ',' '\n' > "${DATASET}_subset.txt"
  
  if [[ ! -d $DATASET && -s "${DATASET}_subset.txt" ]]
  then
    bsub -env "all, DATASET=$DATASET, SUBSET=${DATASET}_subset.txt" < $SCRIPT
  else
    echo "Directory $DATASET exists or subset file is empty. Skipping..."
  fi
done < "$INPUT_FILE"

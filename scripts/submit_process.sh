#!/bin/bash -e

# Ensure correct number of arguments
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <list_of_datasets>"
  exit 1
fi

INPUT_FILE=$1
SCRIPT=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/scripts/reprocess.bsub
truncate -s 0 finished.tsv
truncate -s 0 runlist.txt

while IFS=$'\t' read -r DATASET SPECIE NUM_ALL NUM_10X SAMPLES; do
  # write subset list to file
  echo $SAMPLES | tr ',' '\n' >"${DATASET}_subset.txt"

  if [[ ! -d $DATASET && -s "${DATASET}_subset.txt" ]]; then
    echo $DATASET >>runlist.txt
  else
    echo "Directory $DATASET exists or subset file is empty. Skipping..."
  fi
done <"$INPUT_FILE"

# Get the number of datasets to process
NUM=$(wc -l <runlist.txt)

# Check if there are any datasets to process
if [ "$NUM" -eq 0 ]; then
  echo "No datasets to process."
  exit 0
fi

# Submit the job to the LSF queue
bsub -J "reprocess.datasets[1-${NUM}]%40" -env "all, ENV_DATASET_LIST=runlist.txt" <"$SCRIPT"

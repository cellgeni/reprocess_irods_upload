#!/bin/bash -e

INPUT_FILE=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/v1.todo_head100.tsv
SCRIPT=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/scripts/reprocess.bsub
: > finished.tsv

while IFS=$'\t' read -r DATASET SPECIE NUM_ALL NUM_10X SAMPLES
do  
    echo $SAMPLES | tr ',' '\n' > "${DATASET}_subset.txt"
    bsub -env "all, DATASET=$DATASET, SUBSET=${DATASET}_subset.txt" < $SCRIPT
done < "$INPUT_FILE"
#!/bin/bash

script=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/reprocess_public_10x/scripts/collect_metadata.sh
dataset_dir=/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/datasets

cp /lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/reprocess_public_10x/scripts/curl* .

for dataset_path in $dataset_dir/*
do
	dataset=$(basename $dataset_path)
	echo "Download metadata for $dataset"
	$script $dataset
	mv $dataset* $dataset_path/
done

rm curl*
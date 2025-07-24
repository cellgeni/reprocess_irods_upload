#!/bin/bash

# Find all *solo_qc* files in the archive
ilocate /archive/cellgeni/datasets/% | grep solo_qc > solo_qc.list

# Create a directory to store the files
for file in $(cat solo_qc.list)
do
  iget -K $file ./solo_qc_dir/
  echo $file
done
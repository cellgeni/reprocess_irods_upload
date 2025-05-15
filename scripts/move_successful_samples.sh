#!/bin/bash

# Check if the right number of arguments is passed
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <successful_sample_list>"
  exit 1
fi

# Define paths
successful_sample_list=$1
target_dir="/lustre/scratch127/cellgen/cellgeni/reprocessing-datasets-project/irods"

# Add newline at the end if needed
sed -i -e '$a\' $successful_sample_list

# Create the target directory if it doesn't exist
mkdir -p "$target_dir"

# Read each directory from the list and move it
while IFS=$'\t' read -r SAMPLE DATASET DIR; do
  # Check if sample directory exists
  sample_dir="$DIR/$SAMPLE"
  echo ""
  echo "Processing sample: $SAMPLE, dataset: $DATASET, directory: $DIR"
  if [[ ! -d "$sample_dir" ]]; then
    echo "Directory $sample_dir does not exist, skipping."
    continue
  fi

  # Create a dataset directory in dataset directory
  target_dataset_dir="$target_dir/$DATASET"
  mkdir -p "$target_dataset_dir"

  # Copy the sample directory to the target dataset directory
  cp -r "$sample_dir" "$target_dataset_dir/"
  echo "Moved $sample_dir to $target_dataset_dir/"

  # Check if exists _SRATtmp directory and notify user if it does
  if [[ -d "$sample_dir/_SRATtmp" ]]; then
    echo "Warning: _SRATtmp directory exists in for SAMPLE=$SAMPLE, DATASET=$DATASET. Please check."
  fi

  # Copy family.soft, sdrf, idf, project.list files if they exist and were not already copied
  for file in _family.soft .sdrf.txt. .idf.txt .project.list; do
    src_file="$DIR/$DATASET$file"
    if [[ -f "$src_file" && ! -f "$target_dataset_dir/$DATASET.$file" ]]; then
      cp "$src_file" "$target_dataset_dir/"
      echo "Copied $src_file to $target_dataset_dir/"
    elif [[ ! -f "$src_file" ]]; then
      echo "File $src_file does not exist, skipping."
    fi
  done

  # Create solo_qc file if there is no existing one and copy header from filtered_solo_qc
  solo_qc_file="$target_dataset_dir/$DATASET.solo_qc.tsv"
  if [[ ! -f "$solo_qc_file" ]]; then
    head -n 1 "$DIR/$DATASET.solo_qc.tsv" >"$solo_qc_file"
    echo "Created $solo_qc_file from $filtered_solo_qc"
  fi

  # Append ena.tsv sample.list sample_x_run.tsv run.list accessions.tsv parsed.tsv sra.tsv ena.tsv sample.relation.list url.list and solo_qc.tsv files
  echo "$SAMPLE" >"$target_dataset_dir/$DATASET.sample.list"
  grep "$SAMPLE" "$DIR/$DATASET.sample_x_run.tsv" >>"$target_dataset_dir/$DATASET.sample_x_run.tsv"
  grep "$SAMPLE" "$DIR/$DATASET.sample_x_run.tsv" | awk '{print $2}' | sed 's/,/\n/g' >"$target_dataset_dir/$SAMPLE.run.list"
  cat "$target_dataset_dir/$SAMPLE.run.list" >>"$target_dataset_dir/$DATASET.run.list"
  grep "$SAMPLE" "$DIR/$DATASET.accessions.tsv" >>"$target_dataset_dir/$DATASET.accessions.tsv"
  grep -f "$target_dataset_dir/$SAMPLE.run.list" "$DIR/$DATASET.parsed.tsv" >>"$target_dataset_dir/$DATASET.parsed.tsv"
  grep -f "$target_dataset_dir/$SAMPLE.run.list" "$DIR/$DATASET.sra.tsv" >>"$target_dataset_dir/$DATASET.sra.tsv"
  grep -f "$target_dataset_dir/$SAMPLE.run.list" "$DIR/$DATASET.ena.tsv" >>"$target_dataset_dir/$DATASET.ena.tsv"
  grep "$SAMPLE" "$DIR/$DATASET.sample.relation.list" >>"$target_dataset_dir/$DATASET.sample.relation.list"
  grep "$SAMPLE" "$DIR/$DATASET.solo_qc.tsv" >>"$solo_qc_file"
  grep -f "$target_dataset_dir/$SAMPLE.run.list" "$DIR/$DATASET.urls.list" >>"$target_dataset_dir/$DATASET.urls.list"

  # Remove the temporary sample run list file
  rm "$target_dataset_dir/$SAMPLE.run.list"

  echo "Copied Sample info for $SAMPLE"

done <"$successful_sample_list"

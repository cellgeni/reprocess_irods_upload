#!/usr/bin/env bash

set -euo pipefail

# Usage: cleanup.sh <filter_dataset_list> <pass_samples_list>
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <filter_dataset_list> <pass_samples_list>"
  exit 1
fi

filter_file="$1"
pass_samples_file="$2"

# 1) Make sure necessary input files exist
if [[ ! -f "$filter_file" ]]; then
  echo "ERROR: $filter_file not found!"
  exit 1
fi

if [[ ! -f "$pass_samples_file" ]]; then
  echo "ERROR: $pass_samples_file not found!"
  exit 1
fi

# 2) Loop through datasets that had at least one passing sample
while IFS= read -r dataset_dir; do
  # Check if the directory is valid
  if [[ ! -d "$dataset_dir" ]]; then
    echo "WARNING: $dataset_dir is not a directory. Skipping..."
    continue
  fi

  echo "Processing dataset: $dataset_dir"
  cd "$dataset_dir"

  # 3) Remove GSM* or SRR* directories not in pass_samples_file
  for d in GSM* SRR* ERS*; do
    if [[ -d "$d" ]]; then
      # If this directory name is NOT found in pass_samples_file, remove it
      if ! grep -Fxq "$d" "$pass_samples_file"; then
        echo "  Removing $d"
        rm -rf "$d"
      fi
    fi
  done

  cd - >/dev/null

done <"$filter_file"

echo "Cleanup complete."

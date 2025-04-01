#!/usr/bin/env bash

set -euo pipefail

# Usage check
if [[ $# -ne 4 ]]; then
  echo "Usage: $0 <input_dataset_list> <filter_dataset_list> <pass_samples_list> <completely_failed_list>"
  exit 1
fi

input_file="$1"
filter_file="$2"
pass_samples_file="$3"
failed_file="$4"

# 1) Make sure the input file of dataset directories exists
if [[ ! -f "$input_file" ]]; then
  echo "ERROR: Could not find $input_file"
  exit 1
fi

# 2) Initialize/empty the output files
>"$filter_file"
>"$pass_samples_file"
>"$failed_file"

# 3) Loop over each dataset directory from input_file
while IFS= read -r dataset_dir; do
  # Use find to locate solo_qc.tsv anywhere *inside* this dataset directory
  # -print -quit stops at the first match found
  solo_qc_file="$(find "$dataset_dir" -type f -name "*solo*qc.tsv" -print -quit || true)"

  # If find returned nothing, the dataset is considered "completely failed"
  if [[ -z "$solo_qc_file" ]]; then
    echo "ERROR: Could not find solo_qc.tsv in $dataset_dir"
    echo "$dataset_dir" >>"$failed_file"
    continue
  fi

  # Extract samples with no empty columns (ignoring header line)
  pass_samples="$(awk -F'\t' 'NR>1 {
    missing=0
    for(i=1; i<=NF; i++){
      if($i == ""){
        missing=1
        break
      }
    }
    if(!missing) print $1
  }' "$solo_qc_file")"

  # If no samples pass, dataset is failed
  if [[ -z "$pass_samples" ]]; then
    echo "$dataset_dir" >>"$failed_file"
  else
    # Otherwise, record the dataset in filter_file
    echo "$dataset_dir" >>"$filter_file"
    # And append each passing sample to pass_samples_file
    while IFS= read -r sample; do
      echo "$sample" >>"$pass_samples_file"
    done <<<"$pass_samples"
  fi

done <"$input_file"

# Print filtering stats
all_datasets_count="$(wc -l <"$input_file")"
passing_datasets_count="$(wc -l <"$filter_file")"
passing_samples_count="$(wc -l <"$pass_samples_file")"

echo "Filtering complete."
echo "All datasets: $all_datasets_count"
echo "Passing datasets: $passing_datasets_count"
echo "Passing samples: $passing_samples_count"
echo
echo "Wrote to:"
echo "  - $filter_file"
echo "  - $pass_samples_file"
echo "  - $failed_file"

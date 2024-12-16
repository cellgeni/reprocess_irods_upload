#!/bin/bash

# Check if a directory path is provided
if [[ -z "$1" ]]; then
    echo "Usage: $0 <path_to_log_directory>"
    exit 1
fi

LOGDIR=$1

# Output file
output_file="job_summary.tsv"
echo -e "DATASET\tCOMPLETED\tSTART_TIME\tTERMINATE_TIME\tLOG_PATH" > "$output_file"

# Loop through output*.log files
for output_log in $LOGDIR/output*.log; do
    # Extract job ID from file name
    job_id=$(basename $output_log | grep -oP '\d+')
    
    # Check if file exists
    if [[ -f "$output_log" ]]; then
        # Extract Start and Terminate times
        start_time=$(grep -oP "Started at \K.*" "$output_log")
        terminate_time=$(grep -oP "Terminated at \K.*" "$output_log")
        
        # Check completion status
        completed=$(grep -q "Successfully completed." "$output_log" && echo "Yes" || echo "No")
    fi

    # Corresponding error log
    error_log="$LOGDIR/error${job_id}.log"
    if [[ -f "$error_log" ]]; then
        # Extract dataset name from error log
        dataset=$(grep -oP "Using file \K[^ ]*_subset\.txt" "$error_log" | sed 's/_subset\.txt//')
    else
        dataset="Unknown"
    fi

    # Write results to output file
    echo -e "${dataset}\t${completed}\t${start_time}\t${terminate_time}\t${output_log}" >> "$output_file"
done

echo "Parsing complete. Results written to $output_file."

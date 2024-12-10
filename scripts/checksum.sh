#!/bin/bash

# Input file
INPUT_FILE=$1
OUTPUT_FILE="checksum_results.tsv"

# Ensure output file is empty before appending
echo -e 'dataset\tfilepath\tirodspath\tmd5\tirods_checksum\tstatus' > "$OUTPUT_FILE"

# Read the file line by line
while IFS=$'\t' read -r DATASET LOCAL_PATH IRODS_PATH CHECKSUM
do
    # Calculate MD5 checksum for the irods_path file
    CALCULATED_CHECKSUM=$(ichksum "$IRODS_PATH" | awk '{print $NF}')

    # Compare calculated checksum with the provided one
    if [[ "$CALCULATED_CHECKSUM" == "$CHECKSUM" ]]; then
        STATUS="MATCH"
    else
        STATUS="MISMATCH"
    fi

    # Output results
    echo -e "$DATASET\t$IRODS_PATH\t$CHECKSUM\t$CALCULATED_CHECKSUM\t$STATUS" >> "$OUTPUT_FILE"

done < "$INPUT_FILE"

echo "Checksum verification completed. Results saved to $OUTPUT_FILE"

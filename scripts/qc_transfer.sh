#!/bin/bash

pattern="Successfully completed."
directory=/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/transfer

total_logs=$(find $directory -type f -name "output*.log" | wc -l)
successful_logs=$(find $directory -type f -name "output*.log" -exec grep -q "$pattern" {} \; -print | wc -l)

find "$directory" -type f -name "output*.log" ! -exec grep -q "$pattern" {} \; -print > failed_logs.txt

echo "Total output*.log files: $total_logs"
echo "Files containing 'Successfully completed.': $successful_logs"
echo "Files do not contain 'Successfully completed.': $( wc -l failed_logs.txt )"

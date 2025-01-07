#!/bin/bash

pattern="Successfully completed."
directory=$1
output=$2

total_logs=$(find $directory -type f -name "output*.log" | wc -l)
successful_logs=$(find $directory -type f -name "output*.log" -exec grep -q "$pattern" {} \; -print | wc -l)

find "$directory" -type f -name "output*.log" ! -exec grep -q "$pattern" {} \; -print > $output

echo "Total output*.log files: $total_logs"
echo "Files containing 'Successfully completed.': $successful_logs"
echo "Files do not contain 'Successfully completed.': $( wc -l $output )"

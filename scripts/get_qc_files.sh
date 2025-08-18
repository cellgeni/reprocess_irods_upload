#!/bin/bash

# Find all *solo_qc* files in the archive
echo "Searching for *solo_qc* files in the archive..."
ilocate /archive/cellgeni/datasets/% | grep solo_qc > solo_qc.list

# Create a directory to store the files
mkdir -p solo_qc_dir

# Count total files first
total=$(wc -l < solo_qc.list)

# Use pv to show progress
echo "Total files to download: $total"
echo "Starting download..."
cat solo_qc.list | pv -l -e -r -s $total | while read file; do
    iget -K -f "$file" ./solo_qc_dir/
    echo "Downloaded: $(basename "$file")" >&2
done

echo  # New line after completion
echo "Download complete!"
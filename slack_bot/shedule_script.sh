#!/bin/bash

# Change working directory
cd /lustre/scratch127/cellgen/cellgeni/aljes/reprocess

# Get the list of completed jobs
./scripts/job_summary.sh /lustre/scratch127/cellgen/cellgeni/aljes/reprocess/reprocessing-datasets-project/0_Current >/dev/null
/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/venv/bin/python scripts/qc_reprocessing.py --dirlist logs/completed_list.txt --checklist_file logs/checklist.tsv --pass_file logs/passlist.txt --fail_file logs/faillist.txt >slack_bot/qc_results.txt
wc -l logs/job_summary.tsv >>slack_bot/qc_results.txt
lfs quota -h -g cellgeni /lustre/scratch127/cellgen | grep scratch | awk '{print $2, $4}' >>slack_bot/qc_results.txt

# Post the results to slack
/lustre/scratch127/cellgen/cellgeni/aljes/reprocess/venv/bin/python /lustre/scratch127/cellgen/cellgeni/aljes/reprocess/slack_bot/app.py --file slack_bot/qc_results.txt

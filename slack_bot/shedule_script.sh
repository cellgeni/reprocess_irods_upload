#!/bin/bash

# Change working directory
cd /lustre/scratch127/cellgen/cellgeni/aljes/reprocessing

# Get the list of completed jobs
./scripts/job_summary.sh reprocessed >/dev/null
/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/venv/bin/python scripts/qc_reprocessing.py --dirlist logs/completed_list.txt --checklist_file logs/checklist.tsv --pass_file logs/passlist.txt --fail_file logs/faillist.txt >slack_bot/qc_results.txt
wc -l logs/job_summary.tsv >>slack_bot/qc_results.txt
lfs quota -h -g cellgeni /lustre/scratch124/cellgen | grep - | awk '{print "scratch124 " $1, $3}' >>slack_bot/qc_results.txt
lfs quota -h -g cellgeni /lustre/scratch126/cellgen | grep - | awk '{print "scratch126 " $1, $3}' >>slack_bot/qc_results.txt
lfs quota -h -g cellgeni /lustre/scratch127/cellgen | grep - | awk '{print "scratch127 " $1, $3}' >>slack_bot/qc_results.txt

# Post the results to slack
/lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/venv/bin/python /lustre/scratch127/cellgen/cellgeni/aljes/reprocessing/slack_bot/app.py --file slack_bot/qc_results.txt

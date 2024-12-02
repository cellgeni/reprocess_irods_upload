#!/bin/bash

target=/archive/cellgeni/datasets

while read -r source
do
    bsub -env "all, SOURCE=$source" < transfer_to_irods.bsub
done
#!/usr/bin/env python3

import os
import sys
import argparse
import pandas as pd


def init_parser() -> argparse.ArgumentParser:
    """
    Initialise argument parser for the script
    """
    parser = argparse.ArgumentParser(
        description="Creates cisTopic object from fragments, consensus peaks and quality control files"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Specify a path to the file list of STARsolo QC files to be used. First column should be dataset name, second column should be path to the file. Example: sample1,/path/to/sample1/STARsoloQC.csv",
    )
    parser.add_argument(
        "output",
        metavar="<file>",
        type=str,
        help="Specify a path to the output file. Default: successful_samples.csv",
        default="successful_samples.csv",
    )
    parser.add_argument(
        "--filtered_qc",
        metavar="<file>",
        type=str,
        help="Specify a path to save filtered qc file. Default: filtered_solo_qc.tsv",
        default="filtered_solo_qc.tsv",
    )
    parser.add_argument(
        "--sep",
        metavar="<val>",
        type=str,
        help='Specify a separator for metadata files. Default: ","',
        default=",",
    )
    return parser


def main():
    # Parse arguments
    parser = init_parser()
    args = parser.parse_args()

    # Read file list
    if os.path.exists(args.input):
        with open(args.input, "r") as file:
            file_list = file.readlines()
            file_list = [line.strip().split(args.sep) for line in file_list]

    # Read files to dataframe
    dataframe_list = []
    for dataset, filepath in file_list:
        # Check if the file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} does not exist.")
        # Read the file into a DataFrame
        df = pd.read_csv(filepath, sep="\t")
        if not df.empty:
            # Add a column with the dataset name and directory path
            df["dataset"] = dataset
            df["directory"] = os.path.dirname(filepath)
            # Append the DataFrame to the list
            dataframe_list.append(df)

    # Concatenate all DataFrames into a single DataFrame
    if len(dataframe_list) == 0:
        print("No successful samples found.")
        sys.exit(0)

    successful_samples = pd.concat(dataframe_list, ignore_index=True, axis=0)

    # Filter samples with NaN values
    successful_samples = successful_samples.dropna()

    # Split dataframe in two
    successful_samples_list = successful_samples[
        ["Sample", "dataset", "directory"]
    ].copy()
    filtered_qc = successful_samples.iloc[:, :-2].copy()

    # Save files
    successful_samples_list.to_csv(args.output, sep="\t", index=False, header=False)
    filtered_qc.to_csv(args.filtered_qc, sep="\t", index=False)


if __name__ == "__main__":
    main()

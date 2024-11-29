#!/usr/bin/env python3

import os
from typing import Dict, List, Any, Tuple
import argparse

# GLOBAL VARIABLES
TARGET_KEYS = [
    "sample",
    "experiment",
    "run",
    "Rd_all",
    "WL",
    "Species",
    "Paired",
    "Strand",
]

KEY_CONVERT = {"Rd_all": "total_reads", "WL": "whitelist"}


def init_parser() -> argparse.ArgumentParser:
    """
    Initialise argument parser for the script
    """
    parser = argparse.ArgumentParser(
        description="Creates cisTopic object from fragments, consensus peaks and quality control files"
    )
    parser.add_argument(
        "sourcedir",
        type=str,
        help="Specify a path to the directory to be you want to get metadata from",
    )
    parser.add_argument(
        "--outputdir",
        metavar="<dir>",
        type=str,
        help="Specify a path to the output directory. Default: metadata",
        default="metadata",
    )
    parser.add_argument(
        "--sep",
        metavar="<val>",
        type=str,
        help="Specify a separator for metadata files. Default: \\t",
        default="\t",
    )
    return parser


def accessions_row_to_meta(row: str) -> Dict[str, List]:
    """
    Convert a row from accessions.tsv file to dict
    Args:
        row (str): row from accessions.tsv file

    Returns:
        Dict[str, List]: a list of experiments and runs is saved to the Dict
    """
    sample_dict = {
        "sample": row[1],
        "experiment": row[2].split(","),
        "run": row[3].split(","),
    }
    return sample_dict


def solo_qc_row_to_meta(header: List[str], row: str) -> Dict[str, str]:
    """
    A row from solo_qc.tsv file is converted to Dict
    Args:
        header (List[str]): header of solo_qc.tsv file
        row (str): a row of solo_qc.tsv file

    Returns:
        Dict[str, str]: a dict with a row metadata from solo_qc.tsv file
    """
    return dict(zip(header[1:], row[1:]))


def get_accessions_meta(accessions_file: str, sep="\t") -> Dict[str, Dict]:
    """
    Convert accessions.tsv file's rows to Dict
    Args:
        accessions_file (str): a path to accessions.tsv file
        sep (str, optional): separator used to split accessions.tsv file. Defaults to '\t'.

    Returns:
        Dict[str, Dict: a dict with metadata from rows of accessions.tsv file
    """
    with open(accessions_file, "r") as file:
        # split line and remove \n
        lines = [line.rstrip().split(sep) for line in file.readlines()]
        # convert to Dict[sample, meta]
        samples = {
            (line[1] if line[0] == "-" else line[0]): accessions_row_to_meta(line)
            for line in lines
        }
    return samples


def get_solo_qc_meta(solo_qc_file: str, sep="\t") -> Dict[str, Dict]:
    """
    Convert solo_qc.tsv file's rows to Dict
    Args:
        solo_qc_file (str): a path to solo_qc.tsv file
        sep (str, optional): separator used to split solo_qc.tsv file. Defaults to '\t'.

    Returns:
        Dict[str, Dict]: a dict with metadata from rows of solo_qc.tsv file
    """
    with open(solo_qc_file, "r") as file:
        header = file.readline().rstrip().split(sep)
        # split line and remove \n
        lines = [line.rstrip().split(sep) for line in file.readlines()]
        # convert to Dict[sample, meta]
        meta = {line[0]: solo_qc_row_to_meta(header, line) for line in lines}
    return meta


def write_meta(
    meta: List[Dict],
    output_dir: str,
    target_keys: List[str],
    key_convert: Dict[str, str],
    sep="\t",
) -> None:
    """
    Writes metadata from `meta` list to separate files
    Args:
        meta (Dict[str, Any]): a list with metadata entries for each sample
        output_dir (str): a path to output dir
        target_keys (List[str]): a list of keys that should be included in resulting file
        key_convert (Dict[str, str]): a dict to map names from meta to the target names
        sep (str, optional): a separator used to write metadata files. Defaults to '\t'.
    """
    for sample_meta in meta:
        # get sample accession number
        sample_accession_number = sample_meta["sample_accession_number"]
        # filter redundunt keys, change key names if neccessary and convert keys to lower case
        filtered_meta = {
            key_convert.get(key, key).lower(): value
            for key, value in sample_meta.items()
            if key in target_keys
        }
        # convert dict into lines (if there are several values for the same key then several lines are created)
        lines = [
            f"{key}{sep}{val}\n"
            for key, values in filtered_meta.items()
            for val in (values if isinstance(values, list) else [values])
        ]
        # get a filepath to metadata
        filepath = os.path.join(output_dir, f"{sample_accession_number}.tsv")
        # write metadata
        with open(filepath, "w") as file:
            file.writelines(lines)


def main():
    # parse script arguments
    parser = init_parser()
    args = parser.parse_args()

    # get source dir path and dataset name
    source_dir = args.sourcedir.rstrip("/")
    dataset = os.path.basename(source_dir)

    # get paths of files with metadata
    accessions_file = os.path.join(source_dir, f"{dataset}.accessions.tsv")
    solo_qc_file = os.path.join(source_dir, f"{dataset}.solo_qc.tsv")

    # get meta from metadata files
    accessions_meta = get_accessions_meta(accessions_file)
    solo_qc_meta = get_solo_qc_meta(solo_qc_file)

    # concatenate dicts
    meta = [
        dict(sample_accession_number=key, **accessions_meta[key], **solo_qc_meta[key])
        for key in solo_qc_meta.keys()
    ]

    # make output directory
    os.makedirs(args.outputdir, exist_ok=True)

    # write metadata
    write_meta(meta, args.outputdir, TARGET_KEYS, KEY_CONVERT, sep=args.sep)


if __name__ == "__main__":
    main()

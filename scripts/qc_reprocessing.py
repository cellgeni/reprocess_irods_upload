#!/usr/bin/env python3

import os
import sys
import glob
import argparse
import pandas as pd
from typing import List, Dict, Optional, Callable
from itertools import chain
from functools import wraps


METAFILE_SUFFIXES = ["run.list", "sample.list", "sample_x_run.tsv", "parsed.tsv"]
DB_METAFILE_SUFFIXES = [".idf.txt", ".sdrf.txt", "_family.soft"]

INFORMATIVE_COLUMNS = [
    "meta_exist",
    "db_meta_exist",
    "missing_runs_samples",
    "all samples have runs",
    "all runs in run.list",
    "all samples in sample.list",
    "all runs in parsed.list",
    "fastqdir_nonemptyexist",
    "all_fastq_samples",
    "all_fastq_runs_exist",
    "starsolo_allnonemptyexist",
    "starsolo_existOutput",
    "starsolo_existFinalLog",
    "starsolo_noTmp",
    "solo_qc_exists",
    "solo_qc_nonempty",
    "solo_qc_all_samples",
]

ADDITIONAL_COLUMNS = [
    "meta_lost",
    "missing_runs_fastq_samples",
    "missing_fastq_samples",
    "missing_starsolo_samples",
    "starsolo_emptyOutput_samples",
    "starsolo_noFinalLog_samples",
    "starsolo_existTmp_samples",
    "missing_solo_qc_samples",
    "solo_qc_mapped_samples",
]

MUST_BE_TRUE_COLUMNS = [
    "meta_exist",
    "missing_runs_samples",
    "all runs in run.list",
    "all samples in sample.list",
    "all runs in parsed.list",
    "starsolo_allnonemptyexist",
    "starsolo_existOutput",
    "starsolo_existFinalLog",
    "starsolo_noTmp",
    "solo_qc_exists",
    "solo_qc_nonempty",
    "solo_qc_all_samples",
]


def init_parser() -> argparse.ArgumentParser:
    """
    Initializes and returns the argument parser.

    Args:
        None

    Returns:
        argparse.ArgumentParser: The initialized argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validates a set of reprocessed datasets"
    )
    parser.add_argument(
        "--source",
        metavar="<dir>",
        type=str,
        help="Specify a path where reprocessed datasets are stored",
    )
    parser.add_argument(
        "--dirlist",
        metavar="<file>",
        type=str,
        help="Specify a path to the list of datasets to validate",
    )
    parser.add_argument(
        "--checklist_file",
        metavar="<file>",
        type=str,
        help="Specify a name for the checklist file. Default: checklist.tsv",
        default="checklist.tsv",
    )
    parser.add_argument(
        "--pass_file",
        metavar="<file>",
        type=str,
        help="Specify a name for the file with a list of datasets that passed validation. Default: passlist.txt",
        default="passlist.txt",
    )
    parser.add_argument(
        "--fail_file",
        metavar="<file>",
        type=str,
        help="Specify a name for the file with a list of datasets that failed validation. Default: faillist.txt",
        default="faillist.txt",
    )
    parser.add_argument(
        "--sep",
        metavar="<val>",
        type=str,
        help="Specify a separator for checklist file. Default: \\t",
        default="\t",
    )
    return parser


def validate_checklist_values(func: Callable) -> Callable:
    """
    Decorator that ensures the checklist is valid before calling the wrapped function.

    Args:
        func (Callable): The function to wrap.

    Returns:
        Callable: The wrapped function that validates the checklist before calling func.
    """

    @wraps(func)
    def wrapper(checklist: Dict[str, Optional[bool]], *args, **kwargs) -> None:
        if isinstance(checklist, dict) and all(
            value in (True, None) for value in checklist.values()
        ):
            func(checklist, *args, **kwargs)

    return wrapper


def check_if_dataset(dataset_path: str) -> bool:
    """
    Check if directory name suggests a valid dataset and if path is a directory.

    Args:
        dataset_path (str): The path to check.

    Returns:
        bool: True if directory name suggests a valid dataset, otherwise False.
    """
    dataset_name = os.path.basename(dataset_path)
    is_dataset_name = (
        lambda dn: ("GSE" in dn) or ("E-MTAB" in dn) or ("PRJNA" in dn) or ("SDY" in dn)
    )
    return is_dataset_name(dataset_name) and os.path.isdir(dataset_path)


def get_datasets(args: argparse.Namespace) -> List[str]:
    """
    Return a list of dataset paths based on args.source or args.dirlist.

    Args:
        args (argparse.Namespace): The command-line arguments.

    Returns:
        List[str]: A list of dataset paths.
    """
    if args.dirlist:
        with open(args.dirlist, "r") as file:
            dataset_paths = [path.rstrip() for path in file.readlines()]
        if len(dataset_paths) == 0:
            print("No datasets found in the list")
            sys.exit()
    else:
        dataset_paths = glob.glob(f"{args.source.rstrip('/')}/*")
        dataset_paths = [dp for dp in dataset_paths if check_if_dataset(dp)]
    return dataset_paths


def make_full_path(basedir: str, dataset: str, filename: str) -> str:
    """
    Return the full path for a given dataset and filename.

    Args:
        basedir (str): The base directory.
        dataset (str): The dataset name.
        filename (str): The filename.

    Returns:
        str: The constructed full path.
    """
    return os.path.join(basedir, dataset, filename)


def exist_nonempty(path: str, type: str = "file") -> bool:
    """
    Return True if file or directory at path is non-empty.

    Args:
        path (str): The file or directory path to check.
        type (str, optional): The type of checking ('file' or 'dir'). Defaults to 'file'.

    Returns:
        bool: True if the specified path is non-empty, False otherwise.
    """
    if type == "file":
        return os.path.isfile(path) and os.path.getsize(path) > 0
    elif type == "dir":
        return os.path.isdir(path) and os.listdir(path)
    else:
        raise ValueError


# @validate_checklist_values
def check_metafiles_exist(
    checklist: Dict[str, Optional[bool]],
    basedir: str,
    datasetname: str,
    metafile_suffixes: List[str],
) -> None:
    """
    Check if metadata files exist and update checklist.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        basedir (str): The base directory.
        datasetname (str): The dataset name.
        metafile_suffixes (List[str]): The list of metafile suffixes.

    Returns:
        None
    """
    checklist.update({"meta_exist": True, "meta_lost": None})
    meta_paths = [
        make_full_path(basedir, datasetname, f"{datasetname}.{suffix}")
        for suffix in metafile_suffixes
    ]
    lost_files = [file for file in meta_paths if not exist_nonempty(file, type="file")]
    if lost_files:
        checklist["meta_exist"] = False
        checklist["meta_lost"] = ",".join(lost_files)


def check_db_meta_exist(
    checklist: Dict[str, Optional[bool]],
    basedir: str,
    datasetname: str,
    db_meta_suffixes: List[str],
) -> None:
    """
    Check if database metadata files exist and update checklist.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        basedir (str): The base directory.
        datasetname (str): The dataset name.
        db_meta_suffixes (List[str]): The list of database metadata file suffixes.

    Returns:
        None
    """
    db_meta_paths = [
        make_full_path(basedir, datasetname, f"{datasetname}{suffix}")
        for suffix in db_meta_suffixes
    ]
    exist_list = [exist_nonempty(file, type="file") for file in db_meta_paths]
    checklist["db_meta_exist"] = any(exist_list)


def read_sample_x_run(filepath: str) -> Dict[str, Optional[List[str]]]:
    """
    Read sample-to-run mapping from file and return a dict.

    Args:
        filepath (str): The path to the sample_x_run file.

    Returns:
        Dict[str, Optional[List[str]]]: A dictionary mapping samples to their run IDs.
    """
    process_line = lambda line: line.rstrip().split("\t", 1)
    with open(filepath, "r") as file:
        splited_lines = list(map(process_line, file.readlines()))
        sample_to_run = {
            line[0]: (line[1].split(",") if len(line) == 2 else None)
            for line in splited_lines
        }
    return sample_to_run


def get_first_column(filepath: str) -> List[str]:
    """
    Return the list of first column values from a file.

    Args:
        filepath (str): The path to the file.

    Returns:
        List[str]: A list of values from the first column.
    """
    first_col = lambda line: line.rstrip().split("\t", 1)[0]
    with open(filepath, "r") as file:
        return [first_col(line) for line in file.readlines()]


def validate_file(
    basedir: str, dataset: str, filename: str, correct_list: List[str]
) -> bool:
    """
    Validate that a file matches the provided list of items using set equality.

    Args:
        basedir (str): The base directory.
        dataset (str): The dataset name.
        filename (str): The file to validate.
        correct_list (List[str]): The list of expected items.

    Returns:
        bool: True if the file contents match the expected items, False otherwise.
    """
    filepath = os.path.join(basedir, dataset, filename)
    list_from_file = get_first_column(filepath)
    return set(list_from_file) == set(correct_list)


def check_sample_x_run_file(
    checklist: Dict[str, Optional[bool]], filepath: str
) -> Dict[str, Optional[List[str]]]:
    """
    Read and check the sample_x_run file, update the checklist, and return the mapping.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        filepath (str): The path to the sample_x_run file.

    Returns:
        Dict[str, Optional[List[str]]]: A dictionary mapping samples to their run IDs.
    """
    sample_to_run = read_sample_x_run(filepath)
    samples_with_lost_runs = [
        key for key, value in sample_to_run.items() if value is None
    ]
    checklist["all samples have runs"] = not samples_with_lost_runs
    checklist["missing_runs_samples"] = (
        ",".join(samples_with_lost_runs) if samples_with_lost_runs else None
    )
    return sample_to_run


# @validate_checklist_values
def check_metafiles(
    checklist: Dict[str, Optional[bool]],
    basedir: str,
    dataset: str,
    sample_to_run: Dict[str, Optional[List[str]]],
) -> None:
    """
    Validate the presence of run.list, sample.list, and parsed.tsv files.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        basedir (str): The base directory.
        dataset (str): The dataset name.
        sample_to_run (Dict[str, Optional[List[str]]]): A dictionary mapping samples to their run IDs.

    Returns:
        None
    """
    samples = list(sample_to_run.keys())
    runs = list(chain.from_iterable(sample_to_run.values()))

    checklist["all runs in run.list"] = validate_file(
        basedir, dataset, f"{dataset}.run.list", runs
    )
    checklist["all samples in sample.list"] = validate_file(
        basedir, dataset, f"{dataset}.sample.list", samples
    )
    checklist["all runs in parsed.list"] = validate_file(
        basedir, dataset, f"{dataset}.parsed.tsv", runs
    )


# @validate_checklist_values
def validate_fastqs(
    checklist: Dict[str, Optional[bool]],
    basedir: str,
    dataset: str,
    sample_to_runs: Dict[str, Optional[List[str]]],
) -> None:
    """
    Check the fastqs directory presence and contents.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        basedir (str): The base directory.
        dataset (str): The dataset name.
        sample_to_runs (Dict[str, Optional[List[str]]]): A dictionary mapping samples to their run IDs.

    Returns:
        None
    """
    samples = set(sample_to_runs.keys())
    fastqdir_path = os.path.join(basedir, dataset, "fastqs")
    if exist_nonempty(fastqdir_path, type="dir"):
        checklist["fastqdir_nonemptyexist"] = True
        lost_samples = samples.difference(os.listdir(fastqdir_path))
        if not lost_samples:
            checklist["all_fastq_samples"] = True
            fastqnum_persample = {
                s: len(os.listdir(os.path.join(fastqdir_path, s))) for s in samples
            }
            lostrun_samples_list = [
                s
                for s in samples
                if fastqnum_persample[s] / 2 != len(sample_to_runs[s])
            ]
            if not lostrun_samples_list:
                checklist["all_fastq_runs_exist"] = True
            else:
                checklist["all_fastq_runs_exist"] = False
                checklist["missing_runs_fastq_samples"] = lostrun_samples_list
        else:
            checklist["all_fastq_samples"] = False
            checklist["missing_fastq_samples"] = ",".join(lost_samples)
    else:
        checklist["fastqdir_nonemptyexist"] = False


def validate_starsolo(
    checklist: Dict[str, Optional[bool]],
    basedir: str,
    dataset: str,
    sample_to_runs: Dict[str, Optional[List[str]]],
) -> None:
    """
    Validate the presence and completeness of STARsolo outputs.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        basedir (str): The base directory.
        dataset (str): The dataset name.
        sample_to_runs (Dict[str, Optional[List[str]]]): A dictionary mapping samples to their run IDs.

    Returns:
        None
    """
    samples = set(sample_to_runs.keys())
    not_ok_dirs = [
        s
        for s in samples
        if not exist_nonempty(os.path.join(basedir, dataset, s), type="dir")
    ]
    if not not_ok_dirs:
        checklist["starsolo_allnonemptyexist"] = True
        no_output_dirs = [
            s
            for s in samples
            if not exist_nonempty(
                os.path.join(basedir, dataset, s, "output"), type="dir"
            )
        ]
        no_final_log_file = [
            s
            for s in samples
            if not exist_nonempty(
                os.path.join(basedir, dataset, s, "Log.final.out"), type="file"
            )
        ]
        tmp_exists = [
            s
            for s in samples
            if exist_nonempty(os.path.join(basedir, dataset, s, "_STARtmp"), type="dir")
        ]
        checklist["starsolo_existOutput"] = not bool(no_output_dirs)
        checklist["starsolo_emptyOutput_samples"] = (
            ",".join(no_output_dirs) if no_output_dirs else None
        )
        checklist["starsolo_existFinalLog"] = not bool(no_final_log_file)
        checklist["starsolo_noFinalLog_samples"] = (
            ",".join(no_final_log_file) if no_final_log_file else None
        )
        checklist["starsolo_noTmp"] = not bool(tmp_exists)
        checklist["starsolo_existTmp_samples"] = (
            ",".join(tmp_exists) if tmp_exists else None
        )
    else:
        checklist["starsolo_allnonemptyexist"] = False
        checklist["missing_starsolo_samples"] = ",".join(not_ok_dirs)


def validate_solo_qc(
    checklist: Dict[str, Optional[bool]],
    basedir: str,
    dataset: str,
    sample_to_runs: Dict[str, Optional[List[str]]],
) -> None:
    """
    Validate the presence and content of the solo_qc.tsv file.

    Args:
        checklist (Dict[str, Optional[bool]]): The dictionary tracking validation statuses.
        basedir (str): The base directory.
        dataset (str): The dataset name.
        sample_to_runs (Dict[str, Optional[List[str]]]): A dictionary mapping samples to their run IDs.

    Returns:
        None
    """
    samples = set(sample_to_runs.keys())
    solo_qc_path = os.path.join(basedir, dataset, f"{dataset}.solo_qc.tsv")
    checklist["solo_qc_exists"] = exist_nonempty(solo_qc_path, type="file")
    if checklist["solo_qc_exists"]:
        with open(solo_qc_path, "r") as file:
            lines = file.readlines()
            checklist["solo_qc_nonempty"] = bool(len(lines) - 1)
        if checklist["solo_qc_nonempty"]:
            samples_in_file = get_first_column(solo_qc_path)[1:]
            lost_samples = samples.difference(samples_in_file)
            checklist["solo_qc_all_samples"] = not bool(lost_samples)
            checklist["missing_solo_qc_samples"] = (
                ",".join(lost_samples) if lost_samples else None
            )
            # find mapping fraction column index
            header = lines[0].rstrip().split("\t")
            column_idx = header.index("all_u+m")

            # get mapped samples
            mapped_samples = [
                samples_in_file[i]
                for i, line in enumerate(lines[1:])
                if len(header) == len(line.rstrip().split("\t"))
                and float(line.rstrip().split("\t")[column_idx]) > 0.5
            ]
            checklist["solo_qc_mapped_samples"] = ",".join(mapped_samples)


def validate_basedir(
    dataset_paths: List[str],
    checklist_columns: List[str],
    metafile_suffixes: List[str],
    db_metafile_suffixes: List[str],
) -> pd.DataFrame:
    """
    Validate all datasets in dataset_paths and return a DataFrame with results.

    Args:
        dataset_paths (List[str]): A list of dataset paths to validate.
        checklist_columns (List[str]): A list of columns to include in the checklist.
        metafile_suffixes (List[str]): A list of metadata file suffixes.
        db_metafile_suffixes (List[str]): A list of database metadata file suffixes.

    Returns:
        pd.DataFrame: A DataFrame containing the checklist results for each dataset.
    """
    checklist_dict: Dict[str, Dict[str, Optional[bool]]] = {}
    for dataset_path in dataset_paths:
        dataset, basedir = os.path.basename(dataset_path), os.path.dirname(dataset_path)
        checklist = {col: None for col in checklist_columns}
        check_metafiles_exist(checklist, basedir, dataset, metafile_suffixes)
        if isinstance(checklist, dict) and all(
            value in (True, None) for value in checklist.values()
        ):
            sample_x_run_path = os.path.join(
                basedir, dataset, f"{dataset}.sample_x_run.tsv"
            )
            sample_to_run = check_sample_x_run_file(checklist, sample_x_run_path)
            check_metafiles(checklist, basedir, dataset, sample_to_run)
            validate_fastqs(checklist, basedir, dataset, sample_to_run)
            validate_starsolo(checklist, basedir, dataset, sample_to_run)
            validate_solo_qc(checklist, basedir, dataset, sample_to_run)
            check_db_meta_exist(checklist, basedir, dataset, db_metafile_suffixes)
        checklist_dict[dataset] = checklist
    return pd.DataFrame(checklist_dict).T.sort_index()


def main() -> None:
    """
    The main entry point for the QC reprocessing script.

    Args:
        None

    Returns:
        None
    """
    parser = init_parser()
    args = parser.parse_args()
    if args.source is None and args.dirlist is None:
        parser.print_help()
        sys.exit()
    dataset_paths = get_datasets(args)
    dataset_path_dict = {os.path.basename(dp): dp for dp in dataset_paths}
    checklist_columns = INFORMATIVE_COLUMNS + ADDITIONAL_COLUMNS
    checklist_df = validate_basedir(
        dataset_paths, checklist_columns, METAFILE_SUFFIXES, DB_METAFILE_SUFFIXES
    )
    pass_list = checklist_df[
        checklist_df[MUST_BE_TRUE_COLUMNS].all(axis=1)
    ].index.tolist()
    fail_list = checklist_df.index.difference(pass_list).tolist()
    print(
        f"PASS: {len(pass_list)}, FAIL: {len(fail_list)}, ALL: {checklist_df.shape[0]}"
    )
    with pd.option_context("future.no_silent_downcasting", True):
        checklist_df = checklist_df.fillna("-").infer_objects()
    checklist_df.to_csv(args.checklist_file, sep=args.sep)
    with open(args.pass_file, "w") as passfile:
        pass_list = [dataset_path_dict[dataset] for dataset in pass_list]
        passfile.write("\n".join(pass_list) + "\n")
    with open(args.fail_file, "w") as failfile:
        fail_list = [dataset_path_dict[dataset] for dataset in fail_list]
        failfile.write("\n".join(fail_list) + "\n")


if __name__ == "__main__":
    main()

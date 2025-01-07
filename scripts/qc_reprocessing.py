#!/usr/bin/env python3

import os
import sys
import glob
import argparse
import pandas as pd
from itertools import chain
from functools import wraps


METAFILE_SUFFIXES = ["run.list", "sample.list", "sample_x_run.tsv", "parsed.tsv"]
DB_METAFILE_SUFFIXES = [".idf.txt", ".sdrf.txt", "_family.soft"]

INFORMATIVE_COLUMNS = [
    "meta_exist",
    "db_meta_exist",
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
]

MUST_BE_TRUE_COLUMNS = [
    "meta_exist",
    "missing_runs_smaples",
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
    Initialise argument parser for the script
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


def validate_checklist_values(func):
    @wraps(func)
    def wrapper(checklist, *args, **kwargs):
        # Ensure the first argument is a dictionary
        if isinstance(checklist, dict) and all(
            value in (True, None) for value in checklist.values()
        ):
            func(checklist, *args, **kwargs)

    return wrapper


def check_if_dataset(dataset_path):
    dataset_name = os.path.basename(dataset_path)
    is_dataset_name = (
        lambda dataset_name: ("GSE" in dataset_name)
        or ("E-MTAB" in dataset_name)
        or ("PRJNA" in dataset_name)
        or ("SDY" in dataset_name)
    )
    return is_dataset_name(dataset_name) and os.path.isdir(dataset_path)


def get_datasets(args):
    if args.dirlist:
        with open(args.dirlist, "r") as file:
            dataset_paths = [path.rstrip() for path in file.readlines()]
    else:
        dataset_paths = glob.glob(f"{args.source.rstrip('/')}/*")
        # get valid dataset names
        dataset_paths = [
            dataset_path
            for dataset_path in dataset_paths
            if check_if_dataset(dataset_path)
        ]
    return dataset_paths


def make_full_path(basedir, dataset, filename):
    return os.path.join(basedir, dataset, filename)


def exist_nonempty(path, type="file"):
    if type == "file":
        return os.path.isfile(path) and os.path.getsize(path) > 0
    elif type == "dir":
        return os.path.isdir(path) and os.listdir(path)
    else:
        raise ValueError


@validate_checklist_values
def check_metafiles_exist(checklist, basedir, datasetname, metafile_suffixes):
    # draft output dict
    checklist.update({"meta_exist": True, "meta_lost": None})
    # make paths from suffixes
    meta_paths = [
        make_full_path(basedir, datasetname, f"{datasetname}.{meta_suffix}")
        for meta_suffix in metafile_suffixes
    ]
    # find lost files
    lost_files = [file for file in meta_paths if not exist_nonempty(file, type="file")]
    if lost_files:
        checklist["meta_exist"] = False
        checklist["meta_lost"] = ",".join(lost_files)


def check_db_meta_exist(checklist, basedir, datasetname, db_meta_suffixes):
    # make paths from suffixes
    db_meta_paths = [
        make_full_path(basedir, datasetname, f"{datasetname}{meta_suffix}")
        for meta_suffix in db_meta_suffixes
    ]
    # check if exist
    exist_list = [exist_nonempty(file, type="file") for file in db_meta_paths]
    checklist["db_meta_exist"] = any(exist_list)


def read_sample_x_run(filepath):
    process_line = lambda line: line.rstrip().split("\t", 1)
    with open(filepath, "r") as file:
        splited_lines = list(map(process_line, file.readlines()))
        sample_to_run = {
            line[0]: (line[1].split(",") if len(line) == 2 else None)
            for line in splited_lines
        }
    return sample_to_run


def get_first_column(filepath):
    first_col = lambda line: line.rstrip().split("\t", 1)[0]
    with open(filepath, "r") as file:
        first_column_list = [first_col(line) for line in file.readlines()]
    return first_column_list


def validate_file(basedir, dataset, filename, correct_list):
    filepath = os.path.join(basedir, dataset, filename)
    list_from_file = get_first_column(filepath)
    return set(list_from_file) == set(correct_list)


def check_sample_x_run_file(checklist, filepath):
    # read sample x run file
    sample_to_run = read_sample_x_run(filepath)
    # check if all samples have runs
    samples_with_lost_runs = [
        key for key, value in sample_to_run.items() if value is None
    ]
    checklist["all samples have runs"] = not samples_with_lost_runs
    checklist["missing_runs_smaples"] = (
        ",".join(samples_with_lost_runs) if samples_with_lost_runs else None
    )
    return sample_to_run


@validate_checklist_values
def check_metafiles(checklist, basedir, dataset, sample_to_run):
    # get sample to run dict
    samples = list(sample_to_run.keys())
    runs = list(chain.from_iterable(sample_to_run.values()))

    # validate files
    checklist["all runs in run.list"] = validate_file(
        basedir, dataset, f"{dataset}.run.list", runs
    )
    checklist["all samples in sample.list"] = validate_file(
        basedir, dataset, f"{dataset}.sample.list", samples
    )
    checklist["all runs in parsed.list"] = validate_file(
        basedir, dataset, f"{dataset}.parsed.tsv", runs
    )


@validate_checklist_values
def validate_fastqs(checklist, basedir, dataset, sample_to_runs):
    samples = set(sample_to_runs.keys())
    # get fastqdir path
    fastqdir_path = os.path.join(basedir, dataset, "fastqs")
    # check if dir exists
    if exist_nonempty(fastqdir_path, type="dir"):
        checklist["fastqdir_nonemptyexist"] = True
        lost_samples = samples.difference(os.listdir(fastqdir_path))
        # check if all files are present
        if not lost_samples:
            checklist["all_fastq_samples"] = True
            # check if all runs are present
            fastqnum_persample = {
                sample: len(os.listdir(os.path.join(fastqdir_path, sample)))
                for sample in samples
            }
            lostrun_samples_list = [
                sample
                for sample in samples
                if fastqnum_persample[sample] / 2 != len(sample_to_runs[sample])
            ]
            if not lostrun_samples_list:
                checklist["all_fastq_runs_exist"] = True
            else:
                # write missing sample with missing runs
                checklist["all_fastq_runs_exist"] = False
                checklist["missing_runs_fastq_samples"] = lostrun_samples_list
        else:
            # write missing samples to checklist
            checklist["all_fastq_samples"] = False
            checklist["missing_fastq_samples"] = ",".join(lost_samples)

    else:
        checklist["fastqdir_nonemptyexist"] = False


def validate_starsolo(checklist, basedir, dataset, sample_to_runs):
    samples = set(sample_to_runs.keys())
    # check if all starsolo sample dirs exists and not empty
    not_ok_dirs = [
        sample
        for sample in samples
        if not exist_nonempty(os.path.join(basedir, dataset, sample), type="dir")
    ]
    if not not_ok_dirs:
        checklist["starsolo_allnonemptyexist"] = True
        # check there is output dir and no tmp dir
        no_output_dirs = [
            sample
            for sample in samples
            if not exist_nonempty(
                os.path.join(basedir, dataset, sample, "output"), type="dir"
            )
        ]
        no_final_log_file = [
            sample
            for sample in samples
            if not exist_nonempty(
                os.path.join(basedir, dataset, sample, "Log.final.out"), type="file"
            )
        ]
        tmp_exists = [
            sample
            for sample in samples
            if exist_nonempty(
                os.path.join(basedir, dataset, sample, "_STARtmp"), type="dir"
            )
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


def validate_solo_qc(checklist, basedir, dataset, sample_to_runs):
    samples = set(sample_to_runs.keys())
    solo_qc_path = os.path.join(basedir, dataset, f"{dataset}.solo_qc.tsv")
    # check if file exists
    checklist["solo_qc_exists"] = exist_nonempty(solo_qc_path, type="file")
    if checklist["solo_qc_exists"]:
        # check if file is empty
        with open(solo_qc_path, "r") as file:
            lines = file.readlines()
            checklist["solo_qc_nonempty"] = bool(len(lines) - 1)
        # check if all samples are in the file
        if checklist["solo_qc_nonempty"]:
            samples_in_file = get_first_column(solo_qc_path)[1:]
            lost_samples = samples.difference(samples_in_file)
            checklist["solo_qc_all_samples"] = not bool(lost_samples)
            checklist["missing_solo_qc_samples"] = (
                ",".join(lost_samples) if lost_samples else None
            )


def validate_basedir(
    dataset_paths, checklist_columns, metafile_suffixes, db_metafile_suffixes
):
    checklist_dict = dict()
    for dataset_path in dataset_paths:
        dataset, basedir = os.path.basename(dataset_path), os.path.dirname(dataset_path)
        checklist = {col: None for col in checklist_columns}

        # check that all metadata files exist
        check_metafiles_exist(checklist, basedir, dataset, metafile_suffixes)

        # read sample_to_run file
        if isinstance(checklist, dict) and all(
            value in (True, None) for value in checklist.values()
        ):
            sample_x_run_path = os.path.join(
                basedir, dataset, f"{dataset}.sample_x_run.tsv"
            )
            sample_to_run = check_sample_x_run_file(checklist, sample_x_run_path)

            # check that all metadata is consistent and all directories and files exist
            check_metafiles(checklist, basedir, dataset, sample_to_run)

            # validate directories
            validate_fastqs(checklist, basedir, dataset, sample_to_run)

            # validate starsolo output
            validate_starsolo(checklist, basedir, dataset, sample_to_run)

            # validate solo_qc.tsv
            validate_solo_qc(checklist, basedir, dataset, sample_to_run)

            # check that there exists db metadata files
            check_db_meta_exist(checklist, basedir, dataset, db_metafile_suffixes)
        checklist_dict[dataset] = checklist
    return pd.DataFrame(checklist_dict).T.sort_index()


def main():
    # parse script arguments
    parser = init_parser()
    args = parser.parse_args()

    # check if at least one argument is specified
    if args.source is None and args.dirlist is None:
        parser.print_help()
        sys.exit()

    # get dataset paths
    dataset_paths = get_datasets(args)
    dataset_path_dict = {
        os.path.basename(dataset_path): dataset_path for dataset_path in dataset_paths
    }

    # validate directories
    checklist_columns = INFORMATIVE_COLUMNS + ADDITIONAL_COLUMNS
    checklist_df = validate_basedir(
        dataset_paths, checklist_columns, METAFILE_SUFFIXES, DB_METAFILE_SUFFIXES
    )

    # get a list of datasets that passed and failed the QC
    pass_list = checklist_df[
        checklist_df[MUST_BE_TRUE_COLUMNS].all(axis=1)
    ].index.tolist()
    fail_list = checklist_df.index.difference(pass_list).tolist()
    print(
        f"PASS: {len(pass_list)}, FAIL: {len(fail_list)}, ALL: {checklist_df.shape[0]}"
    )

    # write validation results to file
    with pd.option_context("future.no_silent_downcasting", True):
        checklist_df = checklist_df.fillna("-").infer_objects()
    checklist_df.to_csv(args.checklist_file, sep=args.sep)

    # write a list of passed datasets to the file
    with open(args.pass_file, "w") as passfile:
        pass_list = [dataset_path_dict[dataset] for dataset in pass_list]
        passfile.write("\n".join(pass_list))

    # write a list of failed datasets to the file
    with open(args.fail_file, "w") as failfile:
        fail_list = [dataset_path_dict[dataset] for dataset in fail_list]
        failfile.write("\n".join(fail_list))


if __name__ == "__main__":
    main()

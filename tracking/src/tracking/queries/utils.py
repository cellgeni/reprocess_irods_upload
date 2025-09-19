"""Utils for database operations"""

import csv


def read_csv_to_dict_list(filename):
    """Read CSV file and return list of dictionaries (one per row)"""
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.db_utils import db_connect

from pathlib import Path
from sys import argv

from models.abca4_faf_models import Case, FafImage
from utils.io import guess_delimiter, list_to_quoted_str, file_to_list_of_dict
from utils.utils import is_nonempty_file

"""
Load the info from a tsv/csv file into the database.
"""


def arg_parse(required_columns, accepted_columns) -> Path:
    if len(argv) < 2 or argv[1] in ["-h", "--help"]:
        print(f"\nUsage: {argv[0]} <path to the input csv or tsv file>")
        print(f"\tThe table must contain {list_to_quoted_str(required_columns)}.")
        print("\tThe eyes are expected to be labeled as 'OD' or 'OS' in the column 'eye'.")
        print(f"\tOther acceptable input is {list_to_quoted_str(accepted_columns)}.")
        print("\tAny additional columns will be ignored.")
        print()
        exit()

    infile_path = Path(argv[1])
    if not is_nonempty_file(infile_path):
        print(f"{infile_path} does not seem to be a non-empy file. Is the path ok?")
        exit()
    return infile_path


def store_patient_data(data_dict: dict):
    defaults = {}
    if data_dict["onset age"]:
        defaults["onset_age"] = float(data_dict["onset age"])
    if data_dict["is control"]:
        defaults["is_control"] = data_dict["is control"].lower() in ["1", "y", "true"]
    if data_dict["is control"]:
        defaults["haplotype_tested"] = data_dict["haplotype tested"].lower() in ["1", "y", "true"]
    case, created = Case.get_or_create(alias=data_dict["patient alias"], defaults=defaults)
    return case


def store_image_data(image_info: dict):
    images_selected = FafImage.select().where(FafImage.image_path == image_info["image_path"])
    if images_selected.exists():
        # I cannot get more than one entry here because image_path is unique
        FafImage.update(**image_info).where(FafImage.id == images_selected[0].id).execute()
        print(f"updated info for {image_info['image_path']}, image id {images_selected[0].id}")
    else:
        image_created = FafImage.create(**image_info)
        image_created.save()
        print(f"saved {image_info['image_path']} under image id {image_created.id}")


def main():
    required_columns = ["patient alias", "image path", "eye"]
    accepted_columns_patient = ["haplotype tested", "is control", "onset age", "age acquired"]
    accepted_columns_geometry = [
        "width",
        "height",
        "disc x",
        "disc y",
        "macula x",
        "macula y",
    ]
    infile_path = arg_parse(required_columns, accepted_columns_patient + accepted_columns_geometry)
    delimiter = guess_delimiter(infile_path)

    list_of_dict = file_to_list_of_dict(infile_path, delimiter, required_columns)
    db = db_connect()  # this creates db proxy in globals space (that's why we do not use db explicitly)
    for dct in list_of_dict:
        if len(set([k.lower() for k, v in dct.items() if v]).intersection(required_columns)) != len(required_columns):
            column_names_str = ", ".join([f"'{c}'" for c in required_columns])
            print(f"Each row must contain at least {column_names_str} columns filled.")
            print(f"Note that the column names specified in the header must be literally {column_names_str}.")
            exit()

        if not is_nonempty_file(dct["image path"]):
            print(f"{dct['image path']} does not seem to point to a non-empty file.")
            exit()

        case = store_patient_data(dct)

        image_info = {"case_id": case.id, "eye": dct["eye"]}
        if dct.get("age acquired"):
            image_info["age_acquired"] = float(dct["age acquired"])
        for column in accepted_columns_geometry:
            if column not in dct:
                continue
            image_info[column.replace(" ", "_")] = int(dct[column])
        image_info["image_path"] = dct["image path"]

        store_image_data(image_info)

    db.close()


########################
if __name__ == "__main__":
    main()

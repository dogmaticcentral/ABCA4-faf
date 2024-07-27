#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import sys
from math import sqrt

sys.path.insert(0, "..")

from models.abca4_special_tables import OptosLocation


from pprint import pprint

from utils.db_utils import db_connect

from pathlib import Path
from sys import argv

from models.abca4_faf_models import Case, FafImage
from utils.io import guess_delimiter, list_to_quoted_str, file_to_list_of_dict
from utils.utils import is_nonempty_file, scream

"""
Load the info from a tsv/csv file into the database.
"""


def arg_parse(required_columns, accepted_columns) -> Path:
    if len(argv) < 2 or argv[1] in ["-h", "--help"]:
        print(f"\nUsage: {argv[0]} <path to the input csv or tsv file>")
        print(f"\tThe table must contain {list_to_quoted_str(required_columns)}.")
        print(f"\tThese column names should match the provided, case insensitive.")
        print("\tThe eyes are expected to be labeled as 'OD' or 'OS' in the column 'eye'.")
        # print(f"\tOther acceptable input is {list_to_quoted_str(accepted_columns)}.")
        print("\tAny additional columns will be ignored.")
        print()
        exit()

    infile_path = Path(argv[1])
    if not is_nonempty_file(infile_path):
        print(f"{infile_path} does not seem to be a non-empy file. Is the path ok?")
        exit()
    return infile_path


def make_optos_table_if_needed(db):
    if OptosLocation.table_exists():
        print(f"table OptosLocation found in {db.database}")
    else:
        print(f"creating table OptosLocation in {db.database}")
        db.create_tables([OptosLocation])


def parse_location(optos_loaction: str, img_width, img_height):
    # optos locations are given  in the format (example) '1887\\1861'
    # where the full width and the full height are  taken to be 4000
    [rescaled_x, rescaled_y] = [int(coord) for coord in optos_loaction.split('\\')]
    print(rescaled_x, rescaled_y)
    print( img_width, img_height)
    return int(round(rescaled_x/4000*img_width, 0)), int(round(rescaled_y/4000*img_height, 0))


def store_location_data(location_info: dict):
    locations_selected = OptosLocation.select().where(OptosLocation.faf_image_id == location_info["faf_image_id"])
    if locations_selected.exists():
        # I cannot get more than one entry here because image_pmake_optos_table_if_needed()ath is unique
        OptosLocation.update(**location_info).where(OptosLocation.faf_image_id == location_info["faf_image_id"]).execute()
    else:
        optos_location_created = OptosLocation.create(**location_info)
        optos_location_created.save()


def process_and_store(optos_record: dict):
    case = Case.get(Case.alias == optos_record['alias'])
    age = round(float(optos_record['age']), 1)
    faf_image = FafImage.select().where((FafImage.case_id == case)
                                        & (FafImage.eye == optos_record['eye']))
    match  = [f for f in faf_image if round(f.age_acquired, 1) == age]
    if len(match) == 0:
        print(f"no match for")
        pprint(optos_record)
        exit()
    if len(match) > 1:
        print(f"multiple matches for")
        pprint(optos_record)
        for m in match:
            print(m.id, m.image_path)
        exit()

    faf_image_id = match[0].id
    faf_image_width = match[0].width
    faf_image_height = match[0].height
    # print(faf_image_id, faf_image_width, faf_image_height)
    # pprint(optos_record)
    fovea_x, fovea_y = parse_location((optos_record['Optos Fovea Location']), faf_image_width, faf_image_height)
    disc_x, disc_y   = parse_location((optos_record['Optos Optic Disc Location']), faf_image_width, faf_image_height)
    location_info = {
        'faf_image_id': faf_image_id,
        'fovea_location_x': fovea_x,
        'fovea_location_y': fovea_y,
        'disc_location_x': disc_x,
        'disc_location_y': disc_y,
        'fovea_confidence': float(optos_record['Optos Fovea Confidence']),
        'disc_confidence':  float(optos_record['Optos Optic Disc Confidence']),
        'fovea_algorithm': optos_record['Optos Fovea Algorithm']
    }
    # pprint(location_info)
    store_location_data(location_info)


def sanity_check():

    tot_count, ok_count = 0, 0,
    for optos_location in OptosLocation.select():
        # priveate communication from optos:
        # 2000 and 0s are defaults, means their algorith failed
        tot_count += 1
        if optos_location.fovea_location_x == 2000 and optos_location.fovea_location_y == 2000: continue
        if optos_location.disc_location_x ==0 or optos_location.disc_location_y == 0: continue
        f_x =  optos_location.faf_image_id.macula_x
        f_y = optos_location.faf_image_id.macula_y
        d_x =  optos_location.faf_image_id.disc_x
        d_y =  optos_location.faf_image_id.disc_y
        my_disc_distance = sqrt((f_x - d_x)**2 +  (f_y - d_y)**2)
        print()
        print( optos_location.faf_image_id.image_path)
        print(optos_location.id, f"{my_disc_distance:.0f}")
        print("fovea", optos_location.fovea_confidence)
        err_x = abs(optos_location.fovea_location_x - f_x)/my_disc_distance
        print("\tx", optos_location.fovea_location_x, f_x, f"{err_x:.2f}")
        err_y = abs(optos_location.fovea_location_y - f_y)/my_disc_distance
        print("\ty", optos_location.fovea_location_y, f_y, f"{err_y:.2f}")

        print("disc", optos_location.disc_confidence)
        err_x = abs(optos_location.disc_location_x - d_x)/my_disc_distance
        print("\tx", optos_location.disc_location_x, d_x, f"{err_x:.2f}")
        err_y = abs(optos_location.disc_location_y - d_y)/my_disc_distance
        print("\ty", optos_location.disc_location_y, d_y, f"{err_y:.2f}")
        ok_count += 1
    print(tot_count, ok_count)


def main():
    required_columns = ["alias", "eye", "age", "Optos Fovea Algorithm", "Optos Fovea Location",
                        "Optos Fovea Confidence", "Optos Optic Disc Location", "Optos Optic Disc Confidence"]
    required_columns = [r.lower() for r in required_columns]
    infile_path = arg_parse(required_columns, [])
    delimiter = guess_delimiter(infile_path)
    list_of_dict = file_to_list_of_dict(infile_path, delimiter, required_columns)

    db = db_connect()  # this creates db proxy in globals space (that's why we do not use db explicitly)
    make_optos_table_if_needed(db)
    for dct in list_of_dict:
        process_and_store(dct)

    sanity_check()
    db.close()


########################
if __name__ == "__main__":
    main()

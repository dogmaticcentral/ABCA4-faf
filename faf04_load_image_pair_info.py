#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from pathlib import Path
from pprint import pprint
from sys import argv

from models.abca4_faf_models import FafImage, ImagePair
from utils.io import guess_delimiter
from utils.db_utils import db_connect
from utils.utils import is_nonempty_file, scream


def arg_parse() -> Path:
    if len(argv) < 2 or argv[1] in ["-h", "--help"]:
        print(f"\nUsage: {argv[0]} <path to the input csv or tsv file>")
        print(f"\tThe table must contain the 'left eye' and the 'right eye' columns.")
        print(f"\tAny additional columns will be ignored.")
        print()
        exit()

    infile_path = Path(argv[1])
    if not is_nonempty_file(infile_path):
        print(f"{infile_path} does not seem to be a non-empy file. Is the path ok?")
        exit()
    return infile_path


def file_to_list_of_pairs(infile_path, delimiter) -> list[tuple]:
    list_of_pairs = []
    inf = open(infile_path)
    header = None
    for line in inf:
        fields = line.rstrip("\n").split(delimiter)
        if 0 < len(fields) < 2:
            scream(f"there should be at least two columns in this file; instead I am reding:\n{fields}")
            continue
        if not header:
            header = [(" ".join(str(s).lower().split())).strip() for s in fields]
            for column in {'left eye', 'right eye'}.difference(header):
                print(f"I am assuming that this line is the header:")
                print(line)
                print(f"I was expecting to find '{column}' therein")
                exit()
            header = fields
            continue
        images = dict(zip(header, fields))
        if not images['left eye'] or not  images['right eye']: continue
        list_of_pairs.append((images['left eye'], images['right eye']))

    if not header:
        scream(f'no header containing at least 2 columns found.')
        exit(1)

    if len(list_of_pairs) == 0:
        scream(f"{infile_path} seems to contain no image pairs")
        exit(1)

    return list_of_pairs


def get_img_model(db, img_name):
    image_model  = FafImage.get_or_none(image_path=img_name)
    if not image_model:
        print(f"{img_name} not found in {db.__dict__['database']}")
        exit()
    return image_model


def main():
    infile_path = arg_parse()
    delimiter = guess_delimiter(infile_path)
    db = db_connect()  # this creates db proxy in globals space (that's why we do not use db explicitly)
    list_of_pairs = file_to_list_of_pairs(infile_path, delimiter)
    for pair in list_of_pairs:
        [left_eye_img, right_eye_img] = pair
        image_model_left  = get_img_model(db, left_eye_img)
        image_model_right = get_img_model(db, right_eye_img)
        insert_dict = {'left_eye_image_id': image_model_left.id, 'right_eye_image_id': image_model_right.id}
        ImagePair.create(**insert_dict)
    db.close()


########################
if __name__ == "__main__":
    main()

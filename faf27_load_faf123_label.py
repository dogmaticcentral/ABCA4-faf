#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import pandas as pd
from peewee import fn, IntegerField

from models.abca4_faf_models import Case, FafImage
from utils.db_utils import db_connect
from utils.score import image_score, collect_bg_distro_params

from pathlib import Path
from sys import argv
from faf00_settings import WORK_DIR, GEOMETRY, SCORE_PARAMS, USE_AUTO
from models.abca4_special_tables import FAF123Label
from utils.conventions     import construct_workfile_path
from utils.image_utils     import grayscale_img_path_to_255_ndarray, ndarray_to_4channel_png
from utils.utils           import is_nonempty_file, read_simple_hist, scream


def get_alias_to_id_mapping() -> dict:
    """
    Reads the 'cases' table and returns a dictionary mapping alias to Case id.

    Returns:
        dict: A dictionary with alias as keys and Case ids as values.
    """
    alias_id_map = {case.alias: case.id for case in Case.select()}
    return alias_id_map


def make_faf123label_table_if_needed():
    db = db_connect()
    if FAF123Label.table_exists():
        print(f"table FAF123Label found in {db.database}")
    else:
        print(f"creating table FAF123Label in {db.database}")
        db.create_tables([FAF123Label])
    db.close()


def parse_faf123(faf123_file) -> dict:
    print(f"reading {faf123_file}")
    return {}

def store_or_update(image_id, faf123_label, curator):

    label_selected = FAF123Label.select().where(FAF123Label.faf_image_id == image_id, FAF123Label.curator == curator)
    if label_selected.exists():
        update_fields = {"label": faf123_label}
        FAF123Label.update(**update_fields).where(FAF123Label.id == label_selected.id).execute()
    else:
        label_info = {"faf_image_id": image_id, "label": faf123_label, "curator": curator}
        label_created = FAF123Label.create(**label_info)
        label_created.save()


def main():
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <path to faf123.tsv file>")
        exit()

    faf123_file = argv[1]
    if not is_nonempty_file(faf123_file):
        print(f"{faf123_file} not found or may be empty")
        exit()

    make_faf123label_table_if_needed()

    df = pd.read_csv(faf123_file, sep="\t")

    db = db_connect()  # this initializes global proxy
    alias_id_map = get_alias_to_id_mapping()

    for index,  row in df.iterrows():
        alias = row['alias']
        case_id = alias_id_map[alias]
        img_acquired = float(row['image acquired (age, yrs)'])
        image_ids = FafImage.select(FafImage.id).where(
            FafImage.case_id == case_id,
            FafImage.age_acquired > img_acquired*0.999,
            FafImage.age_acquired < img_acquired*1.001,
            FafImage.eye == row['eye']
            )
        image_ids = list(image_ids)
        if len(image_ids) != 1:
            raise Exception("duh ....")
        image_id = image_ids[0].id
        print(alias, case_id, img_acquired, row['eye'], image_id, row['FAF label - Ivana'])
        faf123_label =  row['FAF label - Ivana']
        store_or_update(image_id, faf123_label, "ivana")
    db.close()
########################
if __name__ == "__main__":
    main()

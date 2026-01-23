#! /usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint
from typing import List

import peewee

from models.abca4_faf_models import FafImage, ImagePair
from utils.db_utils import db_connect
from utils.utils import scream, shrug, comfort, is_nonempty_file
from utils.image_utils import grayscale_img_path_to_255_ndarray

"""
Check that the images specified in the database exist, are non-empty,
black and white, that the rgb images specifying the disc, macula, usable,
and the sampling region are present.
"""


def check_image_path(filepath: Path) -> bool:
    print(f"\tchecking the {filepath} filepath")
    if is_nonempty_file(filepath):
        comfort(f"{filepath} OK")
    else:
        scream(f"{filepath} not found or may be empty")
        return False
    return True


def check_image_dimensions(filepath: Path, faf_img_dict: dict) -> bool:
    print(f"\tchecking the image dimensions for {filepath}")
    image_ndarr = grayscale_img_path_to_255_ndarray(filepath)
    (h, w) = image_ndarr.shape
    image_actual = {'height': h, 'width': w}
    # are these dims reasonable numbers?
    if h < 500 or w < 500:
        scream(f"The dimensions ({h}, {w}) are too small for a reasonable analysis.")
        scream(f"\tConsider flagging {filepath} as unusable in the database.")
        return False
    # do the image dims correspond to the numbers stored in the database?
    for dim in ['height', 'width']:
        provided = faf_img_dict.get(dim)

        if provided:
            if image_actual[dim] == provided:
                comfort(f"The image {dim} matches the one found in db. ({image_actual[dim]} px)")
            else:
                scream(f"The image {dim} does not match the one found in db. ({image_actual[dim]} vs {provided}.)")
                return False
        else:
            shrug(f"image {dim} not provided - will store the {dim} from {filepath.name}")
            # TODO this is untested
            update_dict = {dim: image_actual[dim]}
            FafImage.update(**update_dict).where(FafImage.id == faf_img_dict['id']).execute()
            shrug(f"\t{dim} stored for {filepath.name}")
    return True


def check_disc_and_macula(filepath: Path, faf_img_dict: dict) -> bool:
    print(f"\tchecking disc and macula locations for {filepath}")
    for coordinate in ["disc_x", "disc_y", "fovea_x", "fovea_y"]:
        provided = faf_img_dict.get(coordinate)
        if provided:
            comfort(f"{coordinate} provided: {provided}")
            # is the location reasonable?
            upper = faf_img_dict['width'] if "_x" in coordinate else faf_img_dict['height']
            if 0 < provided <= upper:
                comfort(f"{coordinate} value {provided} passes the minimal consistency check.")
            else:
                scream(f"{coordinate} value {provided} does not seem reasonable given the img dim of {upper}.")
                return False
        else:
            scream(f"\t\tdisc and macula locations not provided")
            # shrug(f"{coordinate} provided: {provided}. Labeling {filepath.name} as unusable.")
            # # TODO this is untested
            # FafImage.update(usable=False).where(FafImage.id == faf_img_dict['id']).execute()
            # shrug(f"\tlabeled {filepath.name} as unusable")
    return True


def check_images(filter_condition: peewee.Expression) -> bool:

    filtered_image_objects = list(FafImage.select().where(filter_condition).dicts())
    if len(filtered_image_objects) < 1:
        scream("No images pass the selection from database criterion")
        return False

    for faf_img_dict in filtered_image_objects:
        print(faf_img_dict['image_path'])
        # does the file exist
        faf_image_filepath = Path(faf_img_dict['image_path'])
        if not check_image_path(faf_image_filepath): return False

        # do dimensions in the db match the image dims?
        if not check_image_dimensions(faf_image_filepath, faf_img_dict): return False

        # are the locations of disc and macula provided and reasonable?
        if not check_disc_and_macula(faf_image_filepath, faf_img_dict): return False

        comfort(f"{faf_image_filepath} passed sanity checks")
    return True


def pair_is_match(path1: str, path2: str) -> bool:
    """ If you have a different convention, change the matching criterion here
    :param path1:  full path to img 1, provided as a string
    :param path2:  full path to img 2, provided as a string
    :return bool:  True if the paths satisfy matching criterion
    """
    # TODO find a way to pass the pattern that should match here
    #shrug("image pairs not checked - please provide the criterion")
    #return True
    return (path1.replace("OD", "OX").replace("OS", "OX")
            == path2.replace("OD", "OX").replace("OS", "OX"))


def image_sanity_checks(date_after=None):
    # the checking is a bit slow-ish - check only the latest additions
    print("checking individual images")
    filter_condition: peewee.Expression
    if date_after:
        filter_condition = (FafImage.usable == True)  & (FafImage.updated_date > date_after)
    else:
        filter_condition = (FafImage.usable == True)
    check_images(filter_condition)


def check_pairs():
    for img_pair in ImagePair.select():
        if pair_is_match(img_pair.left_eye_image_id.image_path, img_pair.right_eye_image_id.image_path): continue
        msg = f"The names for the mage pair "
        msg += f"{img_pair.id} (faf image ids {img_pair.left_eye_image_id} and {img_pair.right_eye_image_id})"
        scream(msg)
        scream(img_pair.left_eye_image_id.image_path)
        scream(img_pair.right_eye_image_id.image_path)
    comfort(f"all image pairs match according to the criterion provided in pair_is_match() method.")


def pair_sanity_checks():
    print()
    print("checking image pairs")
    check_pairs()
    print()


def main():
    db = db_connect()
    time_range = datetime.now() - timedelta(days=800)
    if not image_sanity_checks(None):
        exit(1)
    pair_sanity_checks()
    db.close()

########################
if __name__ == "__main__":
    main()

#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from pathlib import Path

from models.abca4_faf_models import FafImage, ImagePair
from utils.db_utils import db_connect
from utils.utils import scream, shrug, comfort, is_nonempty_file
from utils.image_utils import grayscale_img_path_to_255_ndarray

"""
Check that the images specified in the database exist, are non-empty,
black and white, that the rgb images specifying the disc, macula, usable,
and the sampling region are present.
"""


def check_image_path(filepath: Path):
    if is_nonempty_file(filepath):
        comfort(f"{filepath} OK")
    else:
        scream(f"{filepath} not found or may be empty")
        exit(1)


def check_image_dimensions(filepath: Path, faf_img_dict: dict):
    image_ndarr = grayscale_img_path_to_255_ndarray(filepath)
    (h, w) = image_ndarr.shape
    image_actual = {'height': h, 'width': w}
    # are these dims reasonable numbers?
    if h < 500 or w < 500:
        scream(f"The dimensions ({h}, {w}) are too small for a reasonable analysis.")
        scream(f"\tConsider flagging {filepath} as unusable in the database.")
        exit()
    # do the image dims correspond to the numbers stored in the database?
    for dim in ['height', 'width']:
        provided = faf_img_dict.get(dim)

        if provided:
            if image_actual[dim] == provided:
                comfort(f"The image {dim} matches the one found in db. ({image_actual[dim]} px)")
            else:
                scream(f"The image {dim} does not match the one found in db. ({image_actual[dim]} vs {provided}.)")

        else:
            shrug(f"image {dim} not provided - will store the {dim} from {filepath.name}")
            # TODO this is untested
            update_dict = {dim: image_actual[dim]}
            FafImage.update(**update_dict).where(FafImage.id == faf_img_dict['id']).execute()
            shrug(f"\t{dim} stored for {filepath.name}")


def check_disc_and_macula(filepath: Path, faf_img_dict: dict):
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
                exit(1)
        else:
            shrug(f"{coordinate} provided: {provided}. Labeling {filepath.name} as unusable.")
            # TODO this is untested
            FafImage.update(usable=False).where(FafImage.id == faf_img_dict['id']).execute()
            shrug(f"\tlabeled {filepath.name} as unusable")


def check_images():
    any_useable = False
    for faf_img_dict in FafImage.select().where(FafImage.usable == True).dicts():

        any_useable = True
        # does the file exist
        faf_image_filepath = Path(faf_img_dict['image_path'])
        check_image_path(faf_image_filepath)

        # do dimensions in the db match the image dims?
        check_image_dimensions(faf_image_filepath, faf_img_dict)

        # are the locations of disc and macula provided and reasonable?
        check_disc_and_macula(faf_image_filepath, faf_img_dict)

    if not any_useable:
        scream("there seem to be no images labeled as 'usable' in the database")
        exit()

def pair_is_match(path1: str, path2: str) -> bool:
    """ If you have a different convention, change the matching criterion here
    :param path1:  full path to img 1, provided as a string
    :param path2:  full path to img 2, provided as a string
    :return bool:  True if the paths satisfy matching criterion
    """
    shrug("image pairs not checked - please provide the criterion")
    return True
    return path1.replace("OD", "OX").replace("OS", "OX") == path2.replace("OD", "OX").replace("OS", "OX")


def check_pairs():
    for img_pair in ImagePair.select():
        if pair_is_match(img_pair.left_eye_image_id.image_path, img_pair.right_eye_image_id.image_path): continue
        msg = f"The names for the mage pair "
        msg += f"{img_pair.id} (faf image ids {img_pair.left_eye_image_id} and {img_pair.right_eye_image_id})"
        scream(msg)
        scream(img_pair.left_eye_image_id.image_path)
        scream(img_pair.right_eye_image_id.image_path)
        exit(1)


def main():
    db = db_connect()
    check_images()
    check_pairs()
    print()
    db.close()

########################
if __name__ == "__main__":
    main()

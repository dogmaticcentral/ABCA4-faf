#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import math
import sys
sys.path.insert(0, "..")


from models.abca4_faf_models import FafImage

from itertools import product

from faf00_settings import GEOMETRY
from utils.db_utils import db_connect
from utils.vector import Vector


from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import original_2_aux_file_path
from utils.image_utils import rgba_255_path_to_255_ndarray, grayscale_img_path_to_255_ndarray
from utils.utils import is_nonempty_file, scream


class FafCleanView(FafAnalysis):

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image_path = Path(faf_img_dict["image_path"])
        usable_region_path = original_2_aux_file_path(original_image_path, ".usable_region.png")

        for region_png in [original_image_path, usable_region_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()

        return [original_image_path, usable_region_path]

    @staticmethod
    def _ellipse_is_within_usable_region(faf_img_dict, mask) -> bool:
        disc_center = Vector(faf_img_dict["disc_x"], faf_img_dict["disc_y"])
        fovea_center = Vector(faf_img_dict["fovea_x"], faf_img_dict["fovea_y"])
        dist = Vector.distance(disc_center, fovea_center)

        (a, b) = tuple(i * dist for i in GEOMETRY["ellipse_radii"])
        c = math.sqrt(a**2 - b**2)
        u: Vector = (fovea_center - disc_center).get_normalized()
        ellipse_focus_1 = fovea_center + u * c
        ellipse_focus_2 = fovea_center - u * c

        ellipse_is_within_usable_regions = True
        height, width = faf_img_dict["height"], faf_img_dict["width"]
        for y, x in product(range(height), range(width)):
            # the problem is if we have outer ellipse points
            # that fall outside the mask
            if mask[y, x]:
                continue

            # are we within the allipse
            point = Vector(x, y)
            d1 = (point - ellipse_focus_1).getLength()
            d2 = (point - ellipse_focus_2).getLength()
            # no: we are ok
            if d1 + d2 > 2 * a:
                continue
            return False

        return True

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:

        [original_image_path, usable_region_path] = self.input_manager(faf_img_dict)
        mask = rgba_255_path_to_255_ndarray(usable_region_path, channel=2)

        # can I fit the inner ellipse within the usable region?
        view_is_clean = self._ellipse_is_within_usable_region(faf_img_dict, mask)
        if view_is_clean:
            print(f"{original_image_path} has clean view of the inner ellipse")
        else:
            print(f"{original_image_path} is partly covered by artifacts")

        db = db_connect()
        FafImage.update({"clean_view": view_is_clean}).where(FafImage.id == faf_img_dict["id"]).execute()
        db.close()

        return ""


def main():
    """ Use this script for a post hoc labelling of images as artifact free
    (and thus good enough for automated analysis downstream.)
    It relies on the file called <the original im path>.usable_region.png, that is,
    the original image path where hte extension is replaced by usable_region.png'.
    """
    faf_analysis = FafCleanView()
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

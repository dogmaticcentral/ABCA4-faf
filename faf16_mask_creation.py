#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from typing import Callable
import math
from itertools import product
from pathlib import Path

import numpy as np

from classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, GEOMETRY
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.image_utils import rgba_255_path_to_255_ndarray
from utils.score import elliptic_mask
from utils.utils import is_nonempty_file, scream
from utils.vector import Vector


class FafFullMask(FafAnalysis):
    roi_shape = "elliptic"

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument(
            "-c",
            "--ctrl_only",
            dest="ctrl_only",
            action="store_true",
            help="Run for control cases only. Default: False",
        )
        default_shape = "elliptic"
        self.parser.add_argument(
            "-r",
            "--roi-shape",
            dest="roi_shape",
            default=default_shape,
            choices=[default_shape, "peripapillary"],
            help=f"Choice of the region of interest (ROI) shape. Default: {default_shape}.",
        )
        self.parser.add_argument(
            "-l",
            "--outer_ellipse",
            dest="outer_ellipse",
            action="store_true",
            help="Use bigger ellipse radii. Ignored if the ROI region is not elliptic. Default: False.",
        )

    def argv_parse(self):
        super().argv_parse()

        if self.args.roi_shape == "elliptic":
            self.name_stem = "elliptic_mask"
            if self.args.outer_ellipse:
                self.name_stem = "outer_mask"
        elif self.args.roi_shape == "peripapillary":
            self.name_stem = "pp_mask"
        else:
            raise Exception(f"Unrecognized roi shape: {self.roi_shape}")

    ################################################################
    def input_manager(self, faf_img_dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        usable_region = original_2_aux_file_path(original_image, ".usable_region.png")
        blood_vessels = construct_workfile_path(
            WORK_DIR, original_image, alias, "vasculature", "png", should_exist=True
        )

        for region_png in [original_image, usable_region, blood_vessels]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        return [original_image, usable_region, blood_vessels]

    def elliptic_mask(
        self,
        width: int,
        height: int,
        disc_center: Vector,
        macula_center: Vector,
        dist: float,
        usable_img_region: np.ndarray,
        vasculature: np.ndarray,
        outer_ellipse: bool,
    ) -> np.ndarray:
        mask = np.zeros((height, width))

        radii = "outer_ellipse_radii" if outer_ellipse else "ellipse_radii"
        (a, b) = tuple(i * dist for i in GEOMETRY[radii])
        c = math.sqrt(a**2 - b**2)
        u: Vector = (macula_center - disc_center).get_normalized()
        ellipse_focus_1 = macula_center + u * c
        ellipse_focus_2 = macula_center - u * c

        disc_radius  = GEOMETRY["disc_radius"] * dist
        fovea_radius = GEOMETRY["fovea_radius"] * dist

        for y, x in product(range(height), range(width)):
            if not usable_img_region[y, x]:
                continue
            if vasculature[y, x]:
                continue
            point = Vector(x, y)

            # if outside ellipse, continue
            d1 = (point - ellipse_focus_1).getLength()
            d2 = (point - ellipse_focus_2).getLength()
            if d1 + d2 > 2 * a:
                continue

            # if inside disc or fovea, continue
            if Vector.distance(point, macula_center) < fovea_radius:
                continue
            if Vector.distance(point, disc_center) < disc_radius:
                continue
            # finally
            mask[y, x] = 255
        return mask

    def peripapillary_mask(
        self,
        width: int,
        height: int,
        disc_center: Vector,
        macula_center: Vector,
        dist: float,
        usable_img_region: np.ndarray,
        vasculature: np.ndarray,
        outer_ellipse: bool,
    ) -> np.ndarray:
        a = macula_center
        b = outer_ellipse
        mask = np.zeros((height, width))
        disc_radius = GEOMETRY["disc_radius"] * dist
        for y, x in product(range(height), range(width)):
            if not usable_img_region[y, x]:
                continue
            if vasculature[y, x]:
                continue
            point = Vector(x, y)
            dist_from_disc = (point - disc_center).getLength()
            if dist_from_disc < disc_radius:
                continue
            if dist_from_disc > 1.25 * disc_radius:
                continue
            mask[y, x] = 255
        return mask

    ################################################################
    def create_full_mask(self, faf_img_dict: dict, outer_ellipse: bool = False, skip_if_exists: bool = False) -> str:

        if self.args.roi_shape == "peripapillary":
            mask_creator: Callable = self.peripapillary_mask
        else:
            mask_creator: Callable = elliptic_mask

        [original_image, usable_region, blood_vessels] = self.input_manager(faf_img_dict)
        alias = faf_img_dict["case_id"]["alias"]

        outpng = construct_workfile_path(WORK_DIR, original_image, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"found {outpng}")
            return str(outpng)

        disc_center   = Vector(faf_img_dict["disc_x"], faf_img_dict["disc_y"])
        macula_center = Vector(faf_img_dict["macula_x"], faf_img_dict["macula_y"])
        dist = Vector.distance(disc_center, macula_center)

        usable_img_region = rgba_255_path_to_255_ndarray(usable_region, channel=2)
        vasculature = grayscale_img_path_to_255_ndarray(blood_vessels)

        height, width = usable_img_region.shape

        mask = mask_creator(
            width, height, disc_center, macula_center, dist, usable_img_region, vasculature, outer_ellipse
        )
        ndarray_to_int_png(mask, outpng)

        return str(outpng)

    ################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists) -> str:
        """Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict:
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        if self.args.ctrl_only and not faf_img_dict["case_id"]["is_control"]:
            return ""
        return self.create_full_mask(faf_img_dict, outer_ellipse=self.args.outer_ellipse, skip_if_exists=skip_if_exists)


def main():
    description = "Create ROI masks. "
    description += "ROI = inner or outer elliptical region, minus optic disc, fovea, blood vessels and artifacts."
    faf_analysis = FafFullMask(name_stem="elliptic_mask", description=description)
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()


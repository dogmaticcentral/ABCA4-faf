#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from typing import Callable
from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, DEBUG
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png, get_image_dimensions
from utils.image_utils import rgba_255_path_to_255_ndarray
from utils.ndarray_utils import elliptic_mask, peripapillary_mask
from utils.utils import is_nonempty_file, scream, shrug
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

        files_to_check = [original_image]

        usable_region = original_2_aux_file_path(original_image, ".usable_region.png")
        if faf_img_dict["vasculature_detectable"]:
            blood_vessels = construct_workfile_path(WORK_DIR, original_image, alias, "vasculature",
                                                    "png", should_exist=True)
            files_to_check.append(blood_vessels)
        else:
            blood_vessels = None  # if not available, we can do without it

        for region_png in files_to_check:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")

        if not is_nonempty_file(usable_region):
            shrug(f"{usable_region} is nonexistent or empty - the image will be treated as free of artifacts")
            usable_region = None

        return [original_image, usable_region, blood_vessels]

    ################################################################
    def create_full_mask(self, faf_img_dict: dict, outer_ellipse: bool = False, skip_if_exists: bool = False) -> str:

        if self.args.roi_shape == "peripapillary":
            mask_creator: Callable = peripapillary_mask
        else:
            mask_creator: Callable = elliptic_mask

        [original_image_path, usable_region, blood_vessels] = self.input_manager(faf_img_dict)
        alias = faf_img_dict["case_id"]["alias"]

        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            if DEBUG: print(f"found {outpng}")
            return str(outpng)

        disc_center  = Vector(faf_img_dict["disc_x"], faf_img_dict["disc_y"])
        fovea_center = Vector(faf_img_dict["fovea_x"], faf_img_dict["fovea_y"])
        dist = Vector.distance(disc_center, fovea_center)

        usable_img_region = None if usable_region is None else rgba_255_path_to_255_ndarray(usable_region, channel=2)
        vasculature =  None if blood_vessels is None else grayscale_img_path_to_255_ndarray(blood_vessels)

        (width, height) = get_image_dimensions(original_image_path)
        mask = mask_creator(
            width, height, disc_center, fovea_center, dist, usable_img_region, vasculature, outer_ellipse
        )
        ndarray_to_int_png(mask, outpng)
        if DEBUG: print(f"Created {outpng}")

        return str(outpng)

    ################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists) -> str:
        """Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict:
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        return self.create_full_mask(faf_img_dict, outer_ellipse=self.args.outer_ellipse, skip_if_exists=skip_if_exists)


def main():
    description = "Create ROI masks. "
    description += "ROI = inner or outer elliptical region, minus optic disc, fovea, blood vessels and artifacts."
    faf_analysis = FafFullMask(name_stem="elliptic_mask", description=description)
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()


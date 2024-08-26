#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from itertools import product

import numpy as np
from skimage.io import ImageCollection

from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect
from utils.image_utils import ndarray_boolean_to_255_png, grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.vector import Vector

"""
Find and mark blood vessels inside the usable region.
"""
import os


from pathlib import Path
from PIL import Image as PilImage
from PIL import ImageFilter, ImageOps
from skimage import morphology

from classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, DEBUG
from utils.conventions import construct_workfile_path
from utils.pil_utils import extremize_pil
from utils.utils import is_nonempty_file, scream
from utils.ndarray_utils import Ellipse, elliptic_mask, extremize


class FafVasculature(FafAnalysis):

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict["image_path"])
        for region_png in [original_image_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        return [original_image_path]

    def find_vasculature(
        self, original_img_filepath: Path | str, preproc_img_filepath: Path | str, alias: str, skip_if_exists=False
    ) -> str:
        # note we ar using the original image path to construct the new png name
        outpng = construct_workfile_path(WORK_DIR, original_img_filepath, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        else:
            print(f"{os.getpid()} {outpng} started")

        input_pil_image = PilImage.open(str(preproc_img_filepath))
        # this picks vasculature nicely, but with a lot of tiny artifacts around it
        # this could probably be optimized by reducing the image to the elliptic ROI (region of interest)
        # im2 = input_pil_image.filter(ImageFilter.CONTOUR).filter(ImageFilter.ModeFilter())
        im2 = input_pil_image.filter(ImageFilter.ModeFilter()).filter(ImageFilter.CONTOUR)

        if DEBUG:
            im2.save("im2.png")
            print(f"wrote im2.png")

        im3 = ImageOps.grayscale(im2)
        np_array_extremized = extremize_pil(im3, cutoff=230, invert=False)  # not binary, but 0 or 255

        if DEBUG:
            ndarray_to_int_png(np_array_extremized, outfnm := "im3.extr.png")
            print(f"wrote {outfnm}")

        # Area closing removes all _dark_ structures of an image with a surface smaller than area_threshold.
        np_bool_array_closed = morphology.area_closing(np_array_extremized.astype(bool), area_threshold=500, connectivity=3)
        if DEBUG:
            ndarray_to_int_png(np_bool_array_closed.astype(int)*255, outfnm := "im3.closed.png")
            print(f"wrote {outfnm}")

        ndarray_to_int_png((~np_bool_array_closed).astype(int) * 255, outpng)
            
        if is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} done")
            return str(outpng)
        else:
            print(f"{os.getpid()} {outpng} failed")
            return f"vasculature detection in {preproc_img_filepath} failed"

    def inverse_ellipse_mask(self, original_image_path, alias, faf_img_dict):
        """
        Set to 0 everything outside the outer ellipse - an abandoned preprocessing step
        :return: Path
        """
        preprocessed_img_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "vasc_preproc", "png")
        if is_nonempty_file(preprocessed_img_path):
            print(f"found {preprocessed_img_path}")
            return preprocessed_img_path

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        (height, width) = original_image.shape

        fovea_center = Vector(faf_img_dict['fovea_x'], faf_img_dict['fovea_y'])
        disc_center  = Vector(faf_img_dict['disc_x'], faf_img_dict['disc_y'])
        d = Vector.distance(fovea_center, disc_center)

        outer_ellipse_mask = elliptic_mask(width, height, disc_center, fovea_center, d, outer_ellipse=True)
        masked_array   = np.zeros(original_image.shape)*255
        for y, x in product(range(height), range(width)):
            if not outer_ellipse_mask[y, x]: continue
            masked_array[y, x] = original_image[y, x]
        ndarray_to_int_png(masked_array, preprocessed_img_path)
        if DEBUG: print(f"wrote {preprocessed_img_path}")
        return preprocessed_img_path


    def vasc_sanity_check(self,  vasculature_image_path: Path, faf_img_dict):

        # calculate the number of 255 pixels in labeling the vasculature position,
        # and see if we are above some cutoff
        # this is a gadawful way of doing things, but I  have to pretend I do no know where
        # the fovea and disc are, so I don't have much  to go by
        vasculature_image = grayscale_img_path_to_255_ndarray(vasculature_image_path)
        (height, width) = vasculature_image.shape
        vasc_pixels = np.sum(vasculature_image[100:-100, 100:-100])//255
        area = (height-200) * (width-200)
        frac = vasc_pixels/area
        warn = " <=========== " if frac < 1.E-4 else ""
        if not warn: return "OK"

        scream(f'sanity check failed for {vasculature_image_path}')
        scream(f"image size: {area} vasc pixels {vasc_pixels}  fraction {frac:.1E}  {warn}")
        print()
        db = db_connect()
        FafImage.update({"vasculature_detectable": False}).where(FafImage.id == faf_img_dict["id"]).execute()
        db.close()

        return "sanity check failed"

    #######################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict: bool
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """
        [original_image_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict["case_id"]["alias"]

        # preprocessed_img_path = self.inverse_ellipse_mask(original_image_path, alias, faf_img_dict)
        retstr = self.find_vasculature(original_image_path, original_image_path, alias, skip_if_exists)
        if "failed" in retstr:
            return retstr

        return self.vasc_sanity_check(Path(retstr), faf_img_dict)


def main():
    faf_analysis = FafVasculature(name_stem="vasculature")
    faf_analysis.run()


########################
if __name__ == "__main__":

    main()

#!/usr/bin/env python

"""
    © 2024-2026 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import numpy as np

from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png

"""
Find and mark blood vessels inside the usable region.
"""

import os

from pathlib import Path
from PIL import Image as PilImage
from PIL import ImageFilter, ImageOps
from skimage import morphology
from skimage.transform import resize

from faf_classes.faf_analysis import FafAnalysis
from faf00_settings import WORK_DIR, DEBUG
from utils.conventions import construct_workfile_path
from utils.pil_utils import extremize_pil
from utils.utils import is_nonempty_file, scream


class FafVasculature(FafAnalysis):

    def __init__(self, internal_kwargs: dict|None=None, name_stem: str = "vasculature"):
        super().__init__(internal_kwargs=internal_kwargs, name_stem=name_stem)
        description = "A heuristic to detect blood vessels in the input image."
        self.description = description

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict['case_id']['alias']
        eye = faf_img_dict['eye']
        # let's use recalibrated images for blood vessel detection
        recal_image_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "recal",
                                                   eye=eye, filetype="png")
        for region_png in [original_image_path, recal_image_path]:
            if is_nonempty_file(region_png): continue
            msg = f"{region_png} does not exist (or may be empty)."
            if self.args.dry_run:
                scream(msg)
            else:
                raise FileNotFoundError()

        return [original_image_path, recal_image_path]

    def find_vasculature(
        self, faf_img_dict: dict, preproc_img_filepath: Path | str,  skip_if_exists=False
    ) -> str:
        original_img_filepath = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        eye = faf_img_dict["eye"]
        outpng = construct_workfile_path(WORK_DIR, original_img_filepath, alias, self.name_stem, eye=eye, filetype="png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)
        else:
            print(f"{os.getpid()} {outpng} started")

        input_pil_image = PilImage.open(str(preproc_img_filepath))
        width, height = input_pil_image.size
        im1 = input_pil_image.resize((width//3, height//3))
        if DEBUG:
            print(f"DEBUG: new size = {(width//3, height//3)}")
            im1.save(fnm := f"{os.getpid()}.im1.png")
            print(f"DEBUG step: wrote {fnm}")
        # # this picks vasculature nicely, but with a lot of tiny artifacts around it
        # # this could probably be optimized by reducing the image to the elliptic ROI (region of interest)
        # # try a bit of a blur?
        im2 = im1.filter(ImageFilter.CONTOUR)
        if DEBUG:
            im2.save(fnm := f"{os.getpid()}.im2.png")
            print(f"DEBUG step: wrote {fnm}")

        im0 = np.asarray(im2)
        flat = im0.flatten()

        hist, bins = np.histogram(flat, bins=255)
        # completely white and completely black pixels are non-informative - drop
        # normalize to 1
        hist = hist[1:-1] / sum(hist[1:-1])
        cumulative = np.cumsum(hist)

        bottom_fraction = 0.3
        opening_area_threshold = 500
        opening_connectivity = 5
        closing_area_threshold = 50
        closing_connectivity = 2

        # find intensity at which the cumulative fn is the closest to bottom_fraction
        bottom_n_pct_intensity = (np.abs(cumulative - bottom_fraction)).argmin()

        im3 = ImageOps.grayscale(im2)
        np_array_extremized = extremize_pil(im3, cutoff=bottom_n_pct_intensity, invert=False)  # not binary, but 0 or 255

        if DEBUG:
            ndarray_to_int_png(np_array_extremized, outfnm := f"{os.getpid()}.im3.extr.png")
            print(f"DEBUG step: wrote {outfnm}")

        # Area closing removes all _dark_ structures of an image with a surface smaller than area_threshold.
        np_bool_array_open = morphology.area_opening(np_array_extremized.astype(bool),
                                                     area_threshold=opening_area_threshold,
                                                     connectivity=opening_connectivity)
        if DEBUG:
            ndarray_to_int_png(np_bool_array_open.astype(int)*255, outfnm := f"{os.getpid()}.im3.open.png")
            print(f"DEBUG step: wrote {outfnm}")

        np_bool_array_closed = morphology.area_closing(np_bool_array_open,
                                                       area_threshold=closing_area_threshold,
                                                       connectivity=closing_connectivity)
        if DEBUG:
            ndarray_to_int_png(np_bool_array_closed.astype(int)*255, outfnm := f"{os.getpid()}.im3.closed.png")
            print(f"DEBUG step: wrote {outfnm}")

        # ndarray_to_int_png((~np_bool_array_closed).astype(int) * 255, outpng)

        resized_back = resize(np_bool_array_closed, (height, width))
        ndarray_to_int_png((~resized_back).astype(int) * 255, outpng)

        if is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} done")
            return str(outpng)
        else:
            print(f"{os.getpid()} {outpng} failed")
            return f"vasculature detection in {preproc_img_filepath} failed"

    def vasc_sanity_check(self,  vasculature_image_path: Path, faf_img_dict) -> str:

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
        if not warn: return str(vasculature_image_path)

        scream(f'sanity check failed for {vasculature_image_path}')
        scream(f"image size: {area} vasc pixels {vasc_pixels}  fraction {frac:.1E}  {warn}")
        print()

        # create private db connection - handy for multithreading
        local_db = db_connect(initialize_global=False)
        # Use bind_ctx to force FafImage to use this local_db
        # instead of global_db_proxy for this block only.
        with local_db.bind_ctx([FafImage]):
            FafImage.update({"vasculature_detectable": False}).where(FafImage.id == faf_img_dict["id"]).execute()
        # Close explicitly (though context manager usually handles it)
        local_db.close()

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

        [original_image_path, recal_image_path] = self.input_manager(faf_img_dict)

        retstr = self.find_vasculature(faf_img_dict, recal_image_path, skip_if_exists)
        if "failed" in retstr: return retstr

        return self.vasc_sanity_check(Path(retstr), faf_img_dict)


def main():
    faf_analysis = FafVasculature(name_stem="vasculature")
    faf_analysis.run()


########################
if __name__ == "__main__":

    main()

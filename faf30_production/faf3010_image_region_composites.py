#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.db_utils import db_connect

"""
Create composite images consisting of the image being ananlyzed, locations
of the optic disc and macula (fovea), the elliptical regions of interest, and the
background sampling regions.
"""
import os

import numpy as np

from itertools import product
from matplotlib import pyplot as plt
from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from faf00_settings    import WORK_DIR
from utils.conventions import construct_workfile_path, original_2_aux_file_path
from utils.image_utils import grayscale_img_path_to_255_ndarray
from utils.image_utils import rgba_255_path_to_255_ndarray
from utils.image_utils import rgba_255_path_to_255_outline_ndarray
from utils.utils import is_nonempty_file, scream


class FafComposite(FafAnalysis):

    def input_manager(self, faf_img_dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image  = Path(faf_img_dict['image_path'])
        alias = faf_img_dict['case_id']['alias']
        ellipse_overlay = construct_workfile_path(WORK_DIR, original_image, alias, 'overlay',
                                                 eye=faf_img_dict['eye'], filetype= 'png', should_exist=True)
        usable_region   = original_2_aux_file_path(original_image, ".usable_region.png")
        bgsample_region = original_2_aux_file_path(original_image, ".bg_sample.png")
        blood_vessels   = construct_workfile_path(WORK_DIR, original_image, alias, 'vasculature', 'png',
                                                  should_exist=True)

        for region_png in [original_image, usable_region,bgsample_region, blood_vessels]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        return [original_image, ellipse_overlay, usable_region, bgsample_region, blood_vessels]

    ########################################################################
    def compose(self, input_filepaths: list[Path], alias, skip_if_exists=True) -> str:

        [original_image, ellipse_overlay, usable_region, bgsample_region, blood_vessels] = input_filepaths

        outpath = construct_workfile_path(WORK_DIR, original_image, alias, self.name_stem, 'png')
        if skip_if_exists and is_nonempty_file(outpath):
            # print(f"Found non-empty {outpath}. Moving on.")
            return str(outpath)

        img = grayscale_img_path_to_255_ndarray(original_image)
        y_max, x_max = img.shape
        img_color = np.dstack((img, img, img))
        composite = np.zeros((y_max, x_max, 3))

        # the shapes in these files are expected to be filled - we want their  outline instead
        # we expect the polygons to be in the blue channel (2 )
        usable_region_outline = rgba_255_path_to_255_outline_ndarray(usable_region, channel=2)
        bg_sample_outline     = rgba_255_path_to_255_outline_ndarray(bgsample_region, channel=2)
        ellipses_and_disc     = rgba_255_path_to_255_ndarray(ellipse_overlay, channel=0)
        fovea                 = rgba_255_path_to_255_ndarray(ellipse_overlay, channel=1)
        blood_vessels_ndarr   = grayscale_img_path_to_255_ndarray(blood_vessels)
        for y, x  in product(range(y_max), range(x_max)):
            if ellipses_and_disc[y, x] > 0:
                composite[y, x][0] = 255  # grayscale to red
            elif bg_sample_outline[y, x] >  0:
                composite[y, x][1] = 255  # grayscale to green
            elif usable_region_outline[y, x]:
                composite[y, x][2] = 255  # grayscale to blue
            elif fovea[y, x] >  0:
                composite[y, x][1] = 255  # grayscale to green
            elif blood_vessels_ndarr[y, x] > 0:  # make the detect vessels appear white
                for i in range(3): composite[y, x][i] = 255
            else:
                composite[y, x] = img_color[y, x]

        plt.imsave(outpath, composite.astype(np.uint8))
        if is_nonempty_file(outpath):
            print(f"{os.getpid()} {outpath} done")
            return str(outpath)
        else:
            print(f"{os.getpid()} {outpath} failed")
            return f"vasculature detection in {original_image} failed"

    ########################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """ Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict:
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure - generated in compose() function
        """

        # check the presence of all input files that we need
        db = db_connect()
        input_filepaths = self.input_manager(faf_img_dict)
        db.close()
        alias = faf_img_dict['case_id']['alias']
        return self.compose(input_filepaths, alias, skip_if_exists)


def main():
    description = "Creates composite images with locations of optic disc and macula,\n"
    description += "and region of interest, usable region, and background sampling region\n"
    description += "shown in the overlay over the original image. The output format is png."

    faf_analysis = FafComposite(name_stem="composite", description=description)
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

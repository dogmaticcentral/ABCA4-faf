#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.db_utils import db_connect
from utils.score import image_score, collect_bg_distro_params

from itertools import product
from pathlib import Path
from pprint import pprint

import numpy as np

from classes.faf_analysis  import FafAnalysis
from faf00_settings import WORK_DIR, GEOMETRY, SCORE_PARAMS, USE_AUTO
from models.abca4_results  import Score
from utils.conventions     import construct_workfile_path
from utils.fundus_geometry import disc_macula_distance
from utils.gaussian        import gaussian_mixture
from utils.image_utils     import grayscale_img_path_to_255_ndarray, ndarray_to_4channel_png
from utils.utils           import is_nonempty_file, read_simple_hist, scream


def make_score_table_if_needed():
    db = db_connect()
    if Score.table_exists():
        print(f"table Score found in {db.database}")
    else:
        print(f"creating table Score in {db.database}")
        db.create_tables([Score])
    db.close()


class PixelScore(FafAnalysis):

    def create_parser(self):
        super().create_parser()
        default_shape = "elliptic"
        self.parser.add_argument(
            "-r",
            "--roi-shape",
            dest="roi_shape",
            default=default_shape,
            choices=[default_shape, "peripapillary"],
            help=f"Choice of the region of interest (ROI) shape. Default: {default_shape}.",
        )

    def input_manager(self, faf_img_dict) -> list[Path, Path, tuple]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        if USE_AUTO and not faf_img_dict['clean_view']: return [Path(""), Path(""), (0, 0, 0)]

        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        mask_dir = "elliptic_mask" if self.args.roi_shape == "elliptic" else "pp_mask"
        full_mask_path = construct_workfile_path(WORK_DIR, original_image_path, alias, mask_dir, "png")
        bg_stem =  "auto_bg_histogram" if USE_AUTO else "bg_histogram"
        bg_histogram_path = construct_workfile_path(WORK_DIR, original_image_path, alias, bg_stem, "txt")
        for region_png in [original_image_path, full_mask_path, bg_histogram_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()

        bg_distro_params = collect_bg_distro_params(original_image_path, alias, bg_stem)

        return [original_image_path, full_mask_path, bg_distro_params]

    ###################################################################################


    @staticmethod
    def cleaned_up(a, b, upper_bound) -> tuple:
        if a >= b:
            raise f"the first arg ({a}), is expected to be smaller than the second one ({b})."
        a = int(min(max(a, 0), upper_bound))
        b = int(min(max(b, 0), upper_bound))
        return a, b

    @staticmethod
    def score2color(score_matrix) -> np.ndarray:
        height, width = score_matrix.shape[:2]
        black_score_max = int(score_matrix[:, :, 0].max())  # dark pixels in the original image
        white_score_max = int(score_matrix[:, :, 1].max())  # bright pixels in the original image
        outmatrix = np.zeros((height, width, 4))

        for y, x in product(range(height), range(width)):
            if score_matrix[y, x, 0] == 0 and score_matrix[y, x, 1] == 0:
                continue
            outmatrix[y, x, 0] = int(score_matrix[y, x, 0] / black_score_max * 255)
            outmatrix[y, x, 2] = int(score_matrix[y, x, 1] / white_score_max * 255)
            # note: this is an attempt to get rid of the pixelds that appear black in the illustration
            # it does nto affect the score matrix itself
            for color_index in [0, 2]:
                if outmatrix[y, x, color_index] < 20:
                    outmatrix[y, x, color_index] = 0
                elif outmatrix[y, x, color_index] < 100:
                    outmatrix[y, x, color_index] = 100
            outmatrix[y, x, 3] = 255  if (outmatrix[y, x, 0] > 0 or outmatrix[y, x, 2] > 0) else 0

        return outmatrix

    ###########################################################################
    def output_score_png(
        self, faf_img_dict: dict, original_image, alias, score_matrix: np.ndarray, skip_if_exists=False
    ) -> str:
        outpng = construct_workfile_path(WORK_DIR, original_image, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"found {outpng}")
            return str(outpng)

        outmatrix = self.score2color(score_matrix)
        height, width = outmatrix.shape[:2]
        # clip the nd_array to output, tom make the scoring map clearer
        (disc_x, disc_y) = (faf_img_dict["disc_x"], faf_img_dict["disc_y"])
        (macula_x, macula_y) = (faf_img_dict["macula_x"], faf_img_dict["macula_y"])
        unit_dist = disc_macula_distance((disc_x, disc_y), (macula_x, macula_y))
        (x_from, x_to) = (
            macula_x - GEOMETRY["cropping_radii"][0] * unit_dist,
            macula_x + GEOMETRY["cropping_radii"][0] * unit_dist,
        )
        (x_from, x_to) = self.cleaned_up(x_from, x_to, width)
        (y_from, y_to) = (
            macula_y - GEOMETRY["cropping_radii"][1] * unit_dist,
            macula_y + GEOMETRY["cropping_radii"][1] * unit_dist,
        )
        (y_from, y_to) = self.cleaned_up(y_from, y_to, height)
        print(f"writing  {outpng}")
        ndarray_to_4channel_png(outmatrix[y_from:y_to, x_from:x_to, :], outpng)

        return str(outpng)

    def store_or_update(self, image_id, score):

        if self.args.roi_shape == "elliptic":
            target = "pixel_score_auto" if USE_AUTO else "pixel_score"
        elif self.args.roi_shape == "peripapillary":
            target = "pixel_score_peripapillary"
        else:
            raise Exception(f"unrecognized roi shape: {self.args.roi_shape}")

        score_selected = Score.select().where(Score.faf_image_id == image_id)
        if score_selected.exists():
            update_fields = {target: score}
            Score.update(**update_fields).where(Score.faf_image_id == image_id).execute()
        else:
            score_info = {"faf_image_id": image_id, target: score}
            score_created = Score.create(**score_info)
            score_created.save()

    ########################################################################
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        """Inner content of the loop over  faf image data - a convenience for parallelization
        :param faf_img_dict:
        :param skip_if_exists:
            if a nonempty file with the expected name already exists, skip the job
        :return: str
            THe return string indicates success or failure
        """
        if USE_AUTO and not faf_img_dict['clean_view']: return ""
        # check the presence of all input files that we need
        db = db_connect()
        [original_image_path, full_mask_path, bg_distro_params] = self.input_manager(faf_img_dict)
        mask  = grayscale_img_path_to_255_ndarray(full_mask_path)
        make_illustration = self.args.make_slides or self.args.make_pdf
        (score, score_matrix) = image_score(original_image_path, mask, bg_distro_params,
                                            evaluate_score_matrix=make_illustration)
        self.store_or_update(faf_img_dict["id"], score)
        db.close()
        if make_illustration:
            alias = faf_img_dict["case_id"]["alias"]
            return self.output_score_png(faf_img_dict, original_image_path, alias, score_matrix, skip_if_exists)
        else:
            return "ok"


def main():
    make_score_table_if_needed()
    faf_analysis = PixelScore(name_stem="pixel_score")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

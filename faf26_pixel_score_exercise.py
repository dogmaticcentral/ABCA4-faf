#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.db_utils import db_connect
from utils.score import image_score, collect_bg_distro_params

from pathlib import Path

from classes.faf_analysis  import FafAnalysis
from faf00_settings import WORK_DIR, GEOMETRY, SCORE_PARAMS, USE_AUTO
from models.abca4_results import PlaygroundScore
from utils.conventions     import construct_workfile_path
from utils.image_utils     import grayscale_img_path_to_255_ndarray, ndarray_to_4channel_png
from utils.utils           import is_nonempty_file, read_simple_hist, scream


def make_score_table_if_needed():
    db = db_connect()
    if PlaygroundScore.table_exists():
        print(f"table PlaygroundScore found in {db.database}")
    else:
        print(f"creating table PlaygroundScore in {db.database}")
        db.create_tables([PlaygroundScore])
    db.close()


class PixelScore(FafAnalysis):

    def input_manager(self, faf_img_dict) -> list[Path, Path, tuple]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        if USE_AUTO and not faf_img_dict['clean_view']: return [Path(""), Path(""), (0, 0, 0)]

        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        mask_dir = "elliptic_mask"
        full_mask_path = construct_workfile_path(WORK_DIR, original_image_path, alias, mask_dir, "png")
        bg_stem =  "auto_bg_histogram" if USE_AUTO else "bg_histogram"
        bg_histogram_path = construct_workfile_path(WORK_DIR, original_image_path, alias, bg_stem, "txt")
        for region_png in [original_image_path, full_mask_path, bg_histogram_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()

        bg_distro_params = collect_bg_distro_params(original_image_path, alias, bg_stem)

        return [original_image_path, full_mask_path, bg_distro_params]

    def store_or_update(self, image_id, white_weight, black_weight, score):

        target = None
        if white_weight == 0 and black_weight == 1:
            target = "pixel_score_black"
        elif white_weight == 1:
            if black_weight == 0:
                target = "pixel_score_white"
            elif black_weight in [1, 5, 15]:
                target = f"pixel_score_{black_weight}"

        if target is None:
            raise Exception(f"unrecognized wight combination: white {white_weight}, black {black_weight}")

        score_selected = PlaygroundScore.select().where(PlaygroundScore.faf_image_id == image_id)
        if score_selected.exists():
            update_fields = {target: score}
            PlaygroundScore.update(**update_fields).where(PlaygroundScore.faf_image_id == image_id).execute()
        else:
            score_info = {"faf_image_id": image_id, target: score}
            score_created = PlaygroundScore.create(**score_info)
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

        for white_weight, black_weight in [(0, 1)] + [(1, i) for i in [0, 1, 5, 15]]:
            print(faf_img_dict["case_id"]["alias"], white_weight, black_weight)
            (score, score_matrix) = image_score(original_image_path, white_weight, black_weight, mask, bg_distro_params)
            self.store_or_update(faf_img_dict["id"], white_weight, black_weight, score)
        db.close()
        return "ok"

def main():
    make_score_table_if_needed()
    faf_analysis = PixelScore(name_stem="pixel_score")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
import sys

from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect
from faf00_settings import global_db_proxy

sys.path.insert(0, "../..")

from utils.clustering import  disc_and_fovea_detector
from faf00_settings import WORK_DIR

from pathlib import Path

from faf_classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path
from utils.utils import is_nonempty_file


class FafFoveaDisc(FafAnalysis):

    def create_parser(self):
        super().create_parser()
        self.parser.add_argument("-d", '--db-store', dest="store_to_db", action="store_true",
                                 help="Store the fovea and disc locations to database. Default: False.")

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
         :param faf_img_dict:
         :return: list[Path]
         """
        original_image_path  = Path(faf_img_dict['image_path'])
        alias = faf_img_dict["case_id"]['alias']
        eye = faf_img_dict['eye']
        recal_image_path = construct_workfile_path(WORK_DIR, original_image_path, alias,'recal', eye=eye, filetype="png")
        for region_png in [original_image_path, recal_image_path]:
            if not is_nonempty_file(region_png):
                raise FileNotFoundError(f"{region_png} does not exist (or may be empty).")

        return [original_image_path, recal_image_path]


    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        # if not faf_img_dict['clean_view']: return "ok"
        [original_image_path, recal_image_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        eye = faf_img_dict['eye']
        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, eye=eye, filetype="png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        print(f"looking for circular clusters in {recal_image_path}")
        ret = disc_and_fovea_detector(recal_image_path, None, eye, outpng, verbose=False)
        if self.args.store_to_db and ret is not None:
            disc_center, fovea_center = ret
            print(f"storing fovea and disc locations to db for {outpng}, image id {faf_img_dict['id']}")
            if global_db_proxy.obj is None:
                 db = db_connect()
            else:
                 db = global_db_proxy
                 db.connect(reuse_if_open=True)
            update_dict = {"disc_x": disc_center[1], "disc_y": disc_center[0],
                           "fovea_x": fovea_center[1], "fovea_y": fovea_center[0]}
            FafImage.update(**update_dict).where(FafImage.id == faf_img_dict['id']).execute()
        return f"{outpng} ok"


def main():
    # extend faf 12 so that the slides show the ovelays over each image
    faf_analysis = FafFoveaDisc(name_stem="auto_fovea_n_disc")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

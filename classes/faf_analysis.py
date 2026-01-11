from abc import ABC, abstractmethod
from pprint import pprint
from argparse import ArgumentParser, RawDescriptionHelpFormatter as RDF, Namespace
from pathlib import Path
from sys import argv
from typing import Callable

from distributed import Client, LocalCluster
from playhouse.shortcuts import model_to_dict

from faf00_settings import WORK_DIR
from models.abca4_faf_models import FafImage, ImagePair
from faf00_settings import DATABASES
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.reports import make_paired_pdf, make_paired_slides
from utils.utils import shrug, is_nonempty_file


class FafAnalysis(ABC):

    name_stem: str = "faf_analysis"
    args: Namespace = None
    parser: ArgumentParser = None

    def __init__(self, name_stem: str = "faf_analysis", description: str = "Description not provided."):
        self.name_stem = name_stem
        self.description = description
        self.cluster = None

    @abstractmethod
    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        pass

    @abstractmethod
    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        pass

    def create_parser(self):

        self.parser = ArgumentParser(prog=Path(argv[0]).name, description=self.description, formatter_class=RDF)
        self.parser.add_argument("-n", '--n-cpus', dest="n_cpus", type=int, default=1,
                                 help="WIll run one thread per cpu. Default: 1 cpu.")
        self.parser.add_argument("-i", '--image-path', dest="image_path",
                                 help="Image to process. Default: all images in db.")
        self. parser.add_argument("-p", '--pdf', dest="make_pdf", action="store_true",
                                  help="Create a pdf with all images produced. Default: False")
        self.parser.add_argument("-s", '--make_slides', dest="make_slides", action="store_true",
                                 help="Create a set of slides with all images produced. Default: False")
        self.parser.add_argument("-x", '--skip_xisting', dest="skip_xisting", action="store_true",
                                 help="Skip if the resulting image already exists. Default: False")
        self.parser.add_argument("-c", '--ctrl_only', dest="ctrl_only", action="store_true",
                                 help="Process only control images. Default: False.")

    def argv_parse(self):
        self.args = self.parser.parse_args()
        if self.args.n_cpus < 0:
            print(f"{self.args.n_cpus} is not a reasonable number of cpus.")
            exit()
        if self.args.n_cpus > 10:
            print(f"if {self.args.n_cpus} is a reasonable number, please change in argv_parse()")
            exit()

        if self.args.image_path:
            cursor = db_connect()
            faf_img_dicts = list(
                model_to_dict(f) for f in FafImage.select().where(FafImage.image_path == self.args.image_path))
            if len(faf_img_dicts) == 0:  # there cannot be > 1 faf_img_dict for one image path bcs the db field is unique
                print(f"If {self.args.image_path} is the correct image path, please store in the db first.")
                exit()
            if not faf_img_dicts[0]['usable']:
                shrug(f"Keep in mind that int the db {self.args.image_path} is labeled as not usable.")
            cursor.close()
        return self.args

    ################################################################################
    def find_left_and_right_image_pairs(self, all_faf_img_dicts, pngs_produced) -> dict:

        should_be_pair_of = {}
        for image_pair in ImagePair.select():
            left_orig_image  = image_pair.left_eye_image_id.image_path
            right_orig_image = image_pair.right_eye_image_id.image_path
            alias = image_pair.left_eye_image_id.case_id.alias
            left_png  = str(construct_workfile_path(WORK_DIR, left_orig_image, alias, self.name_stem, 'png'))
            right_png = str(construct_workfile_path(WORK_DIR, right_orig_image, alias, self.name_stem, 'png'))
            should_be_pair_of[left_png]  = right_png
            should_be_pair_of[right_png] = left_png

        produced_pairs = {}
        pngs_remaining = pngs_produced.copy()
        for faf_img_dict in all_faf_img_dicts:
            this_orig_img_path = faf_img_dict['image_path']
            alias = faf_img_dict['case_id']['alias']
            this_png = str(construct_workfile_path(WORK_DIR, this_orig_img_path, alias, self.name_stem, 'png'))
            if this_png not in pngs_remaining: continue

            pngs_remaining.remove(this_png)

            paired_png = should_be_pair_of.get(this_png)
            if paired_png in pngs_remaining:
                pngs_remaining.remove(paired_png)
            else:
                paired_png = None

            if this_png and not is_nonempty_file(this_png):
                this_png = None
            if paired_png and not is_nonempty_file(paired_png):
                paired_png =  None

            if this_png is None and paired_png is None: continue

            if alias not in produced_pairs: produced_pairs[alias] = []
            if faf_img_dict['eye'] == "OD":
                produced_pairs[alias].append((this_png, paired_png))
            else:
                produced_pairs[alias].append((paired_png, this_png))

        pairs_sorted = {alias: produced_pairs[alias] for alias in sorted(produced_pairs.keys())}

        return pairs_sorted

    def report(self, all_faf_img_dicts, pngs_produced, name_stem, title):
        db = db_connect()
        if not self.args.make_pdf and not self.args.make_slides: return

        filepath_pairs = self.find_left_and_right_image_pairs(all_faf_img_dicts, pngs_produced)
        if self.args.make_pdf:
            created_file = make_paired_pdf(filepath_pairs, name_stem=name_stem,
                                           title=title, keep_pptx=self.args.make_slides)
            print(f"created {created_file}. Slides kept: {self.args.make_slides}.")
        else:
            created_file = make_paired_slides(filepath_pairs, name_stem=name_stem, title=title)
            print(f"created {created_file}.")
        db.close()

    @staticmethod
    def get_all_faf_dicts():
        # TODO add selction for controls and silverstone only
        return list(model_to_dict(f) for f in FafImage.select().where(FafImage.usable == True))

    def run(self):

        self.create_parser()
        self.argv_parse()

        number_of_cpus = self.args.n_cpus
        img_path = self.args.image_path

        db = db_connect()
        if img_path:
            all_faf_img_dicts = list(model_to_dict(f) for f in FafImage.select().where(FafImage.image_path == img_path))
            number_of_cpus = 1
        else:
            all_faf_img_dicts = self.get_all_faf_dicts()
        db.close()

        # run one round through all images, so we can fail early if something is missing
        # for faf_img_dict in all_faf_img_dicts:  self.input_manager(faf_img_dict)

        # enforce cpu if we are using sqlite
        if DATABASES["default"] == DATABASES["sqlite"] and number_of_cpus > 1:
            shrug("Note: sqlite cannot handle multiple access.")
            shrug("The current implementation does not know how to deal with this.")
            shrug("Please use MySQL or PostgreSQL id you'd like to use the multi-cpu version.")
            shrug("For now, I am proceeding with the single cpu version.")
            number_of_cpus = 1

        # if we got to here, the input is ok
        if number_of_cpus == 1:
            pngs_produced = [self.single_image_job(fd, self.args.skip_xisting) for fd in all_faf_img_dicts]
        else:
            # parallelization # start local workers as processes
            # the cluster should probably created some place else if I can have multiple instatncec of FafAnalysis
            # (can I?)
            cluster = LocalCluster(n_workers=number_of_cpus, processes=True, threads_per_worker=1)
            dask_client = cluster.get_client()
            other_args = {'skip_if_exists': self.args.skip_xisting}
            futures  = dask_client.map(self.single_image_job, all_faf_img_dicts, **other_args)
            pngs_produced = dask_client.gather(futures)
            dask_client.close()

        if any("failed" in r for r in pngs_produced):
            map(print, filter(lambda r: "failed" in r, pngs_produced))
        else:
            print(f"no failure reported while creating images.")
            self.report(all_faf_img_dicts, pngs_produced,
                        name_stem=self.name_stem,
                        title=f"{self.name_stem.capitalize()} images")

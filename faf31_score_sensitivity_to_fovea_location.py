#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import math

from distributed import Client, LocalCluster

from pathlib import Path
from time import time

import numpy as np
from playhouse.shortcuts import model_to_dict
import scipy.stats as stats

from faf00_settings import WORK_DIR
from models.abca4_faf_models import FafImage
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.image_utils import grayscale_img_path_to_255_ndarray
from utils.score import image_score, collect_bg_distro_params
from utils.ndarray_utils import elliptic_mask
from utils.vector import Vector


def create_randomly_displaced_mask(faf_img_dict, displacement_pct) -> np.ndarray:
    disc_center   = Vector(faf_img_dict["disc_x"], faf_img_dict["disc_y"])
    macula_center = Vector(faf_img_dict["macula_x"], faf_img_dict["macula_y"])

    original_dist = Vector.distance(disc_center, macula_center)
    # add a random component to macula and disc_centers
    scale = original_dist*displacement_pct/100
    # disc_center = disc_center + Vector.randomUnitCircle()*scale
    macula_center = macula_center + Vector.randomUnitCircle()*scale
    dist = Vector.distance(disc_center, macula_center)

    (width, height) = (faf_img_dict['width'], faf_img_dict['height'])
    usable_img_region = np.ones((height, width))
    original_image_path = Path(faf_img_dict["image_path"])
    alias = faf_img_dict["case_id"]["alias"]

    vasc_path = construct_workfile_path(WORK_DIR, original_image_path, alias, "vasculature", "png", should_exist=True)
    vasculature = grayscale_img_path_to_255_ndarray(vasc_path)

    return elliptic_mask(width, height, disc_center, macula_center, dist, usable_img_region, vasculature)


def single_image_job(faf_img_dict, displacement_pct) -> tuple:
    original_image_path = Path(faf_img_dict["image_path"])
    alias = faf_img_dict["case_id"]["alias"]
    bg_stem =  "auto_bg_histogram"
    bg_distro_params = collect_bg_distro_params(original_image_path, alias, bg_stem)
    mask = create_randomly_displaced_mask(faf_img_dict, displacement_pct)
    (score, _) = image_score(original_image_path, mask, bg_distro_params)
    time_from_onset = faf_img_dict["age_acquired"] - faf_img_dict["case_id"]["onset_age"]
    return time_from_onset, score


def experiment(faf_img_dicts, displacement_pct, cluster: LocalCluster | None):

    if cluster is None:
        times_scores = [single_image_job(faf_img_dict, displacement_pct) for faf_img_dict in faf_img_dicts]
    else:
        dask_client = cluster.get_client()
        other_args  = {'displacement_pct': displacement_pct}
        futures  = dask_client.map(single_image_job, faf_img_dicts, **other_args)
        times_scores = dask_client.gather(futures)
        dask_client.close()

    times  = [ts[0] for ts in times_scores]
    scores = [ts[1] for ts in times_scores]
    spearman = stats.spearmanr(times, scores)
    return spearman.statistic * 100


def main():
    db = db_connect()
    faf_img_dicts =  list(model_to_dict(f) for f in FafImage.select().where(FafImage.clean_view==True))
    db.close()
    faf_img_dicts = [f for f in faf_img_dicts if not f["case_id"]["is_control"]]

    # none if we do not want to go parallel
    cluster = LocalCluster(n_workers=8, processes=True, threads_per_worker=1)

    # faf_img_dicts = faf_img_dicts[:8]
    outf = open("experiment.tsv", "w")
    print("\t".join(["displacement_pct", "avg)score_corr", "stdev"]), file=outf)

    displacement_pct = 0
    stdev = 0
    score_correlation = experiment(faf_img_dicts, displacement_pct, cluster)
    print(f"displacement pct: {displacement_pct:2d}       score_correlation {score_correlation:.1f}")
    print("\t".join([f"{displacement_pct:2d} ", f"{score_correlation:.1f}", f"{stdev:.1f}"]), file=outf)

    displacement_pcts = [5, 10, 15, 20, 30]
    number_of_experiments = 10
    for displacement_pct in displacement_pcts:
        avg_score_correlation = 0
        avg_sq = 0
        for exp_num in range(number_of_experiments):
            print(f"displacement pct {displacement_pct}, experiment number {exp_num}")
            time0 = time()
            corr = experiment(faf_img_dicts, displacement_pct, cluster)
            avg_score_correlation += corr
            avg_sq += corr**2
            print(f"\t corr =  {corr:.1f}")
            print(f"\t exp done in {(time()-time0)/60:.1f} mins")
        avg_score_correlation /= number_of_experiments
        avg_sq  /= number_of_experiments
        stdev = math.sqrt(avg_sq - avg_score_correlation**2)
        print(f"displacement pct: {displacement_pct:2d}   avg_score_correlation {avg_score_correlation:.1f}  stdev {stdev:.1f}")
        print("\t".join([f"{displacement_pct:2d} ", f"{avg_score_correlation:.1f}", f"{stdev:.1f}"]), file=outf)
    outf.close()


########################
if __name__ == "__main__":
    main()

""" gnuplot:
unset key
set tics font "Helvetica,20"
set lmargin at screen 0.2
set bmargin at screen 0.2
set xrange [-1:32]
set yrange [78:91]
set xlabel "Randomized location of fovea - % of the fovea-disc distance" font "Helvetica,20" offset 0, -2
set ylabel "Corr intensity score vs disease duration\n(Spearman, %)" font "Helvetica,20" offset -15, 0
plot 'experiment.tsv' with yerrorbars pt 7 ps 3


"""
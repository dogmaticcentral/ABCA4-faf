#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from pprint import pprint

import matplotlib.pyplot as plt

from faf00_settings import WORK_DIR
from models.abca4_faf_models import FafImage, Case
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.gaussian import gaussian_mixture
from utils.utils import read_simple_hist
from utils.plot_utils import plot_graph_series


def read_and_normalize(hist_path) -> list[float]:
    values = read_simple_hist(hist_path['main'])
    norm = sum(values)
    probs = [count / norm for count in values]

    # move the whole hsitogram s that the bg vaulaes peak at 100
    bg_hist = read_simple_hist(hist_path['bg'])
    [best_model, weights] = gaussian_mixture(bg_hist, n_comps_to_try=[1])
    bg_mean = best_model.means_[0, 0]
    offset = int(round(bg_mean - 100))
    # shift all values by the offset
    new_probs = probs
    if offset > 0:
        new_probs = probs[offset:] + offset * [0.0]
    elif offset < 0:
        new_probs = (- offset) * [0.0] + probs[:offset]
    return new_probs


def main():
    # TODO - look at the bg histograms, and move all hists so that
    # bg histogram peaks at 100
    # tke the patient alias and the eye from intput line
    # create legend with the matching colors
    # input the name from the cli? or create for all patients?
    alias = "Tony Toothpaste"
    eye = "OS"
    # get the ages from the database
    db = db_connect()
    query = (FafImage
             .select(FafImage.case_id, FafImage.age_acquired, FafImage.image_path).join(Case)
             .where((Case.alias == alias) & (FafImage.eye == eye))
             .order_by(FafImage.age_acquired)
             )

    hist_paths = [
        {"main": construct_workfile_path(WORK_DIR, faf_img.image_path, faf_img.case_id.alias, "roi_histogram", 'txt'),
         "bg": construct_workfile_path(WORK_DIR, faf_img.image_path, faf_img.case_id.alias, "bg_histogram", 'txt'),
         "age": faf_img.age_acquired
         }
        for faf_img in query
    ]
    db.close()
    # pprint(hist_paths)
    histograms = list(map(read_and_normalize, hist_paths))
    labels = [f"  age: {hp['age']} yrs  " for hp in hist_paths]
    colors = [(n / len(histograms), 0, 1 - n / len(histograms)) for n in range(len(histograms))]
    plot_graph_series(histograms, labels, colors, x_label="pixel intensity",
                      plot_title="Progression Of Intensity Distribution Within ROI")


################
if __name__ == "__main__":
    main()

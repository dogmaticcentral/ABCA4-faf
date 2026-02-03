# !/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from utils.conventions import construct_workfile_path
from utils.gaussian import gaussian_mixture
from utils.utils import is_nonempty_file, scream, read_simple_hist

"""
Calculate the pixel score within the mask, and using the correction from the control histograms.
"""
from itertools import product
from pathlib import Path

import numpy as np

from faf00_settings import WORK_DIR, SCORE_PARAMS
from utils.image_utils import grayscale_img_path_to_255_ndarray


def collect_bg_distro_params(bg_histogram_path) -> tuple:

    if not is_nonempty_file(bg_histogram_path):
        scream(f"{bg_histogram_path} does not exist (or may be empty).")
        exit()

    bg_histogram = read_simple_hist(bg_histogram_path)
    bg_model, bg_responsibilities = gaussian_mixture(bg_histogram, n_comps_to_try=[1])
    stdevs = np.sqrt(bg_model.covariances_)
    gradient_correction = SCORE_PARAMS["gradient_correction"]
    return bg_model.means_[0, 0], stdevs[0, 0, 0], gradient_correction


def image_score(
    analyzed_image_path: Path,
    white_pixel_weight: int,
    black_pixel_weight: int,
    mask: np.ndarray,
    bg_distro_params: tuple,
    evaluate_score_matrix=False,
) -> (float, np.ndarray):

    image = grayscale_img_path_to_255_ndarray(analyzed_image_path)

    (bg_mean, bg_stdev, gradient_correction) = bg_distro_params
    score = 0
    height, width = image.shape[:2]
    score_matrix = np.zeros((height, width, 2)) if evaluate_score_matrix else None

    norm = 0
    bg_mean_corrected = bg_mean + gradient_correction
    for y, x in product(range(height), range(width)):
        if not mask[y, x]: continue
        norm += 1
        value = image[y, x]
        if value < bg_mean_corrected:

            pixel_score = black_pixel_weight * (bg_mean_corrected - value)
            if evaluate_score_matrix: score_matrix[y, x, 0] = pixel_score
        else:
            pixel_score = white_pixel_weight * (value - bg_mean_corrected)
            if evaluate_score_matrix: score_matrix[y, x, 1] = pixel_score
        score += pixel_score

    return score / norm, score_matrix

# !/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import math

from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.gaussian import gaussian_mixture
from utils.utils import is_nonempty_file, scream, read_simple_hist
from utils.vector import Vector

"""
Calculate the pixel score within the mask, and using the correction from the control histograms.
"""
from itertools import product
from pathlib import Path

import numpy as np

from faf00_settings import WORK_DIR, GEOMETRY, SCORE_PARAMS, USE_AUTO
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_4channel_png


def collect_bg_distro_params(original_image_path, alias, bg_stem) -> tuple:
    bg_histogram_path = construct_workfile_path(WORK_DIR, original_image_path, alias, bg_stem, "txt")

    if not is_nonempty_file(bg_histogram_path):
        scream(f"{bg_histogram_path} does not exist (or may be empty).")
        exit()

    bg_histogram = read_simple_hist(bg_histogram_path)
    bg_model, bg_responsibilities = gaussian_mixture(bg_histogram, n_comps_to_try=[1])
    stdevs = np.sqrt(bg_model.covariances_)
    gradient_correction = SCORE_PARAMS["gradient_correction"]
    return bg_model.means_[0, 0], stdevs[0, 0, 0], gradient_correction

def elliptic_mask(
        width: int,
        height: int,
        disc_center: Vector,
        macula_center: Vector,
        dist: float,
        usable_img_region: np.ndarray,
        vasculature: np.ndarray,
        outer_ellipse: bool = False,
    ) -> np.ndarray:
        mask = np.zeros((height, width))

        radii = "outer_ellipse_radii" if outer_ellipse else "ellipse_radii"
        (a, b) = tuple(i * dist for i in GEOMETRY[radii])
        c = math.sqrt(a**2 - b**2)
        u: Vector = (macula_center - disc_center).get_normalized()
        ellipse_focus_1 = macula_center + u * c
        ellipse_focus_2 = macula_center - u * c

        disc_radius  = GEOMETRY["disc_radius"] * dist
        fovea_radius = GEOMETRY["fovea_radius"] * dist

        for y, x in product(range(height), range(width)):
            if not usable_img_region[y, x]:
                continue
            if vasculature[y, x]:
                continue
            point = Vector(x, y)

            # if outside ellipse, continue
            d1 = (point - ellipse_focus_1).getLength()
            d2 = (point - ellipse_focus_2).getLength()
            if d1 + d2 > 2 * a:
                continue

            # if inside disc or fovea, continue
            if Vector.distance(point, macula_center) < fovea_radius:
                continue
            if Vector.distance(point, disc_center) < disc_radius:
                continue
            # finally
            mask[y, x] = 255
        return mask

def image_score(
    original_image_path: Path,
    mask: np.ndarray,
    bg_distro_params: tuple,
    evaluate_score_matrix=False,
) -> (float, np.ndarray):

    image = grayscale_img_path_to_255_ndarray(original_image_path)

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
            pixel_score = SCORE_PARAMS["black_pixel_weight"] * (bg_mean_corrected - value)
            if evaluate_score_matrix: score_matrix[y, x, 0] = pixel_score
        else:
            pixel_score = 1 * (value - bg_mean_corrected)
            if evaluate_score_matrix: score_matrix[y, x, 1] = pixel_score
        score += pixel_score

    return score / norm, score_matrix

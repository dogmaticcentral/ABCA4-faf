from faf00_settings import GEOMETRY

_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

import math
from itertools import product
from pathlib import Path
from time import time

import numpy as np

from utils.utils import is_nonempty_file, read_simple_hist
from utils.vector import Vector


noneg = np.vectorize(lambda x: max(0, x))

class Ellipse:
    center: Vector = Vector(0, 0)
    a_point_on_semi_major_axis:  Vector = Vector(1, 0)
    width:  int = 2
    height: int = 1

    def __init__(self, center: Vector, width: int, height: int):
        self.center = center
        self.width  = width
        self.height = height
        

def extremize(pixelmat: np.ndarray,  cutoff=0, invert=False):

    if invert:
        vectorized_fn = np.vectorize(lambda x: 255 if x < cutoff else 0)
    else:
        vectorized_fn = np.vectorize(lambda x: 0 if x < cutoff else 255)

    normalized_pixels = vectorized_fn(pixelmat).astype(np.uint8)

    return normalized_pixels


def in_mask_histogram(image: np.ndarray, mask: np.ndarray, hist_path: str | Path, skip_if_exists: bool = False):
    if skip_if_exists and is_nonempty_file(hist_path):
        histogram = read_simple_hist(hist_path)
        return histogram

    histogram = [0] * 256
    height, width = image.shape
    for y, x in product(range(height), range(width)):
        if not mask[y, x]: continue
        histogram[image[y, x]] += 1
    with open(hist_path, "w") as outf:
        [print(count, file=outf) for count in histogram]
    return histogram


def elliptic_mask(
        width: int,
        height: int,
        disc_center: Vector,
        fovea_center: Vector,
        dist: float,
        usable_img_region: np.ndarray | None = None,
        vasculature: np.ndarray | None = None,
        outer_ellipse: bool = False,
    ) -> np.ndarray:
        mask = np.zeros((height, width))

        radii = "outer_ellipse_radii" if outer_ellipse else "ellipse_radii"
        (a, b) = tuple(i * dist for i in GEOMETRY[radii])
        c = math.sqrt(a**2 - b**2)
        u: Vector = (fovea_center - disc_center).get_normalized()
        ellipse_focus_1 = fovea_center + u * c
        ellipse_focus_2 = fovea_center - u * c

        disc_radius  = GEOMETRY["disc_radius"] * dist
        fovea_radius = GEOMETRY["fovea_radius"] * dist

        for y, x in product(range(height), range(width)):
            if usable_img_region and not usable_img_region[y, x]:
                continue
            if vasculature and  vasculature[y, x]:
                continue
            point = Vector(x, y)

            # if outside ellipse, continue
            d1 = (point - ellipse_focus_1).getLength()
            d2 = (point - ellipse_focus_2).getLength()
            if d1 + d2 > 2 * a:
                continue

            # if inside disc or fovea, continue
            if Vector.distance(point, fovea_center) < fovea_radius:
                continue
            if Vector.distance(point, disc_center) < disc_radius:
                continue
            # finally
            mask[y, x] = 255
        return mask


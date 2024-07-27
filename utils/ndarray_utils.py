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

    def __init__(self, center: Vector,  focus: Vector, width: int, height: int):
        self.center = center
        self.width  = width
        self.height = height
        

def ellipse_to_ndarray(ellipse: Ellipse, img_shape: tuple, outline: False, verbose: False) -> np.ndarray:

    a = ellipse.width
    b = ellipse.height
   
    # focus distance
    c = math.sqrt(a**2 - b**2)
    u: Vector = (ellipse.center - ellipse.a_point_on_semi_major_axis).get_normalized()

    ellipse_focus_1 = ellipse.center + u*c
    ellipse_focus_2 = ellipse.center - u*c

    # this maybe not the most efficient way but is easy to follow:
    # the ellipse is inscribed within a circle of radius = semi_major_axis_length
    x_from = int(ellipse.center.x - a)
    x_to   = int(ellipse.center.x + a)

    y_from = int(ellipse.center.y - a)
    y_to   = int(ellipse.center.y + a)

    time0 = time()
    vf = np.zeros(img_shape)
    for x in range(x_from, x_to+1):
        for y in range(y_from, y_to+1):
            point = Vector(x, y)
            d1 = (point - ellipse_focus_1).getLength()
            d2 = (point - ellipse_focus_2).getLength()
            if outline:
                if d1 + d2 < 2*a-10 or d1 + d2 > 2*a+10: continue
            else:
                if d1 + d2 > 2*a: continue
            vf[y, x] = 1
    if verbose: print(f"time to turn ellipse to matrix: {time()-time0:.2f}")
    return vf


def extremize(pixelmat: np.ndarray,  cutoff=230, invert=False):

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

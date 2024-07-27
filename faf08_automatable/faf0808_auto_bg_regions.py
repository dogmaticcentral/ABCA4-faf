#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import os
import sys
from statistics import mean, stdev

sys.path.insert(0, "..")

import numpy as np

from utils.elliptic import find_equipart_angles
from utils.gaussian import gaussian_mixture


from itertools import product
from math import sqrt, pi
from faf00_settings import GEOMETRY, WORK_DIR
from utils.vector import Vector


from pathlib import Path

from classes.faf_analysis import FafAnalysis
from utils.conventions import construct_workfile_path
from utils.image_utils import grayscale_img_path_to_255_ndarray, ndarray_to_int_png
from utils.utils import is_nonempty_file, scream


class FafAutoBg(FafAnalysis):

    def input_manager(self, faf_img_dict: dict) -> list[Path]:
        """Check the presence of all input files that we need to create the composite img.
        :param faf_img_dict:
        :return: list[Path]
        """
        original_image_path = Path(faf_img_dict["image_path"])
        alias = faf_img_dict["case_id"]["alias"]
        inner_ellipse_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, "elliptic_mask", "png")
        outer_ellipse_path  = construct_workfile_path(WORK_DIR, original_image_path, alias, "outer_mask", "png")

        for region_png in [original_image_path, inner_ellipse_path, outer_ellipse_path]:
            if not is_nonempty_file(region_png):
                scream(f"{region_png} does not exist (or may be empty).")
                exit()
        # TODO check that the outer ellipse and the orig image actually match
        return [original_image_path, inner_ellipse_path, outer_ellipse_path]


    @staticmethod
    def _pointlist_color(point_list: list[tuple], canvas: np.ndarray, color: list):

        for x, y in point_list:
            if x < 0: continue
            if y < 0: continue
            try:
                canvas[y, x] = color
            except Exception as e:
                print(e)
                print(f"row type", type(y))
                print(f"column type", type(x))
                exit()
        return


    @staticmethod
    def _series_of_foci(radial_steps, a0, b0, dist, ellipse_center, u) -> list[tuple]:
        foci = []
        step_size = dist/radial_steps
        for i in range(1, radial_steps+1):
            a = a0 + i*step_size
            b = b0 + i*step_size
            c = sqrt(a**2 - b**2)
            ellipse_focus_1 = ellipse_center + u * c
            ellipse_focus_2 = ellipse_center - u * c
            foci.append((ellipse_focus_1, ellipse_focus_2, a))
        return foci

    @staticmethod
    def _find_shell_index(point: Vector, foci_series):
        shell_index = None
        for index, (ellipse_focus_1, ellipse_focus_2, a) in enumerate(foci_series):
            d1 = (point - ellipse_focus_1).getLength()
            d2 = (point - ellipse_focus_2).getLength()
            if d1 + d2 <= (2 * a)*1.001:  # we have found home
                shell_index = index
                break
        if shell_index is None:
            raise Exception(f"something went wrong with locating the shell that the point {point} belongs to")
        return shell_index

    @staticmethod
    def _find_angular_index(point: Vector, u, angle_series):
        angular_index = None
        angle = Vector.unsigned_angle(u, point)

        for index, angle_bracket_bound in enumerate(angle_series):
            if angle <= angle_bracket_bound:
                angular_index = index
                break

        if angular_index is None:
            raise Exception(f"something went wrong with finding the angle bracket that the point {point} belongs to")

        return angular_index

    def _region_illustration(self, outer_mask, radial_steps, angular_steps, mask):
        colors = [[255, 0, 0], [0, 255, 0],  [0, 0, 255]]
        region_map =  np.dstack((outer_mask, outer_mask, outer_mask))
        outpng = f"{WORK_DIR}/junkyard/region_map.png"
        for shell_index, angular_index in product(range(radial_steps), range(angular_steps)):
            color = colors[(shell_index*radial_steps + angular_index) % len(colors)]
            self._pointlist_color(mask[(shell_index, angular_index)], region_map, color)

        ndarray_to_int_png(region_map, outpng)
        print(f"wrote {outpng}")

    def _collect_region_histograms(self, macula_center, u, radial_steps, angular_steps,
                                   angles, foci_series,  original_image, inner_mask, outer_mask, test=False) -> dict:
        histogram = {}
        test_mask = {}
        for m, n in product(range(radial_steps), range(angular_steps)):
            histogram[(m, n)] = [0]*256
            if test: test_mask[(m, n)] = []

        if test: os.makedirs(f"{WORK_DIR}/junkyard", exist_ok=True)

        (height, width) = original_image.shape

        for y, x in product(range(height), range(width)):
            if not outer_mask[y, x]: continue
            if inner_mask[y, x]: continue
            # ellipse may be rotated - move coords to the system with the origin at macula
            point_moved = Vector(x, y) - macula_center
            shell_index   = self._find_shell_index(point_moved, foci_series)
            angular_index = self._find_angular_index(point_moved, u, angles)
            histogram[(shell_index, angular_index)][original_image[y, x]] += 1
            if test: test_mask[(shell_index, angular_index)].append((x, y))

        if test and test_mask: self._region_illustration(outer_mask, radial_steps, angular_steps, test_mask)
        return histogram

    def _pick_optimal_histogram(self, radial_steps, angular_steps, histogram, faf_img_dict) -> tuple[int, int]:
        peaks = []
        widths = []
        sample_sizes = []
        peak = {}
        width = {}
        sample_size = {}
        for shell_index, angular_index in product(range(radial_steps), range(angular_steps)):
            size = sum(histogram[shell_index, angular_index])
            # gaussian fit does not like t0o few points and neither do I
            if size < 1000: continue
            (fitted_gaussians, weights) = gaussian_mixture(histogram[shell_index, angular_index], n_comps_to_try=[1, 2, 3])
            if fitted_gaussians.n_components > 1: continue
            stdevs = np.sqrt(fitted_gaussians.covariances_)
            # print(f"{shell_index:2d} {angular_index:2d} {fitted_gaussians.means_[0, 0]:6.0f} {stdevs[0, 0, 0]:6.2f} {sample_size:6d}")
            peaks.append(fitted_gaussians.means_[0, 0])
            widths.append(stdevs[0, 0, 0])
            sample_sizes.append(size)
            if shell_index not in peak:
                peak[shell_index] = {}
                width[shell_index] = {}
                sample_size[shell_index] = {}
            peak[shell_index][angular_index] = fitted_gaussians.means_[0, 0]
            width[shell_index][angular_index] = stdevs[0, 0, 0]
            sample_size[shell_index][angular_index] = size

        if len(peaks) == 0:
            msg = "It looks like the bg histogram heuristics will not work for " + faf_img_dict['image_path']
            msg += ": no sample with single gaussian found"
            raise Exception()

        mean_peak = mean(peaks)
        stdev_peak = stdev(peaks)
        mean_width = mean(widths)
        print(f"{mean_peak:10.2f} {stdev_peak:10.2f}")
        print(f"{mean_width:10.2f} {stdev(widths):10.2f}")
        print(f"{mean(sample_sizes):10.2f} {stdev(sample_sizes):10.2f}")

        # limit ourselves to histograms that have the peak in the midrange
        # width average or smaller
        min_dist = 300
        min_shell_index: int = -1
        min_angular_index: int = -1
        for shell_index, angular_index in product(range(radial_steps), range(angular_steps)):
            if shell_index not in peak or angular_index not in peak[shell_index]: continue
            if peak[shell_index][angular_index] < mean_peak - stdev_peak: continue
            if peak[shell_index][angular_index] > mean_peak + stdev_peak: continue
            if width[shell_index][angular_index] > mean_width: continue
            print(f"{shell_index:2d} {angular_index:2d} {peak[shell_index][angular_index]:6.0f} ", end="")
            print(f"{width[shell_index][angular_index]:6.2f} {sample_size[shell_index][angular_index]:6d}")
            # let's try to use the one which is the closes to the average value
            # not sure if it is the best way
            if abs(peak[shell_index][angular_index] - mean_peak) < min_dist:
                min_dist = abs(peak[shell_index][angular_index] - mean_peak)
                min_shell_index = shell_index
                min_angular_index = angular_index
        print('***************')
        print(f"{min_shell_index:2d} {min_angular_index:2d}")

        return min_shell_index, min_angular_index

    def _find_best_bg_rep(self, faf_img_dict, original_image, inner_mask, outer_mask) -> tuple[list, list, int, int]:
        disc_center = Vector(faf_img_dict["disc_x"], faf_img_dict["disc_y"])
        macula_center = Vector(faf_img_dict["macula_x"], faf_img_dict["macula_y"])
        dist = Vector.distance(disc_center, macula_center)

        (a, b) = tuple(i * dist for i in GEOMETRY["ellipse_radii"])
        u: Vector = (macula_center - disc_center).get_normalized()

        [radial_steps, angular_steps] = [10, 15]
        # series of angles that divide ellipse into angle_steps arcs of equal angle
        angles = find_equipart_angles(a, b, angular_steps)

        # series of shells that r can fall within
        foci_series = self._series_of_foci(radial_steps, a, b, dist, Vector(0, 0), u)

        print()
        print(faf_img_dict['image_path'])
        print("collecting histograms")
        histogram = self._collect_region_histograms(macula_center, u, radial_steps, angular_steps,
                                   angles, foci_series,  original_image, inner_mask, outer_mask)

        # which histograms look like nice Gaussians? show very average behavior
        print("fitting Gaussians")

        min_shell_index, min_angular_index = self._pick_optimal_histogram(radial_steps, angular_steps, histogram, faf_img_dict)

        return angles, foci_series, min_shell_index, min_angular_index

    def _write_png(self, original_image, faf_img_dict, inner_mask, outer_mask, angles,
                   foci_series, tgt_angular_index, tgt_shell_index, outpng):
        (height, width) = original_image.shape
        # make empty matrix
        outmatrix = np.zeros((height, width, 4))
        disc_center   = Vector(faf_img_dict["disc_x"], faf_img_dict["disc_y"])
        macula_center = Vector(faf_img_dict["macula_x"], faf_img_dict["macula_y"])
        u: Vector = (macula_center - disc_center).get_normalized()
        # color blue points at the given index
        for y, x in product(range(height), range(width)):
            if not outer_mask[y, x]: continue
            if inner_mask[y, x]: continue
            # ellipse may be rotated - move coords to the system with the origin at macula
            point_moved = Vector(x, y) - macula_center
            angular_index = self._find_angular_index(point_moved, u, angles)
            if angular_index != tgt_angular_index: continue
            shell_index   = self._find_shell_index(point_moved, foci_series)
            if shell_index != tgt_shell_index: continue
            outmatrix[y, x] = [0, 0, 255, 255]
        ndarray_to_int_png(outmatrix, outpng)
        print(f"wrote {outpng}")

    def single_image_job(self, faf_img_dict: dict, skip_if_exists: bool) -> str:
        if not faf_img_dict['clean_view']: return "ok"
        [original_image_path, inner_ellipse_path, outer_ellipse_path] = self.input_manager(faf_img_dict)
        alias = faf_img_dict['case_id']['alias']
        outpng = construct_workfile_path(WORK_DIR, original_image_path, alias, self.name_stem, "png")
        if skip_if_exists and is_nonempty_file(outpng):
            print(f"{os.getpid()} {outpng} found")
            return str(outpng)

        original_image = grayscale_img_path_to_255_ndarray(original_image_path)
        inner_mask = grayscale_img_path_to_255_ndarray(inner_ellipse_path)
        outer_mask = grayscale_img_path_to_255_ndarray(outer_ellipse_path)

        # search elliptic quadrants for one that might contain./
        # a representative background patch
        (angles, foci_series, tgt_shell_index, tgt_angular_index) = self._find_best_bg_rep(faf_img_dict, original_image, inner_mask, outer_mask)

        # store_region_coords as a png
        self._write_png(original_image, faf_img_dict, inner_mask, outer_mask, angles,
                   foci_series, tgt_angular_index, tgt_shell_index, outpng)
        return f"{outpng} ok"


def main():

    faf_analysis = FafAutoBg(name_stem="auto_bg")
    faf_analysis.run()


########################
if __name__ == "__main__":
    main()

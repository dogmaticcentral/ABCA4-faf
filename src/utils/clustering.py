"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from itertools import product
from math import cos, sin, atan, pow, sqrt
from pathlib import Path
from random import sample

import numpy as np

from utils.elliptic import elliptical_mask
from utils.image_utils import channel_visualization, gray_read_blur, rgba_255_path_to_255_ndarray
from utils.utils import scream

BLACK = 1
WHITE = 2
UNASSIGNED = 0

IntPoint  = list[int]
IntPointList = list[IntPoint]


class ClusterBookkeeping:

    # the key in the cluster and color dict will be the label of a cluster - an integer  will do
    # tha value is the list of (x, y) tuple indicating coords of a pixel belonging to the cluster
    # for example { 27: [(1,2), (1,3), (2, 2)]}
    cluster: dict
    # if we are trying to find black and white clusters at the same time, in this dict
    # we keep track of the color of each cluster given its label
    # for example { 27: WHITE}
    color:   dict
    # this is per-pixel info - to which cluster does the pixel at [x, y] position belong to
    label: np.ndarray

    last_label: int
    selected: list
    parametrization: dict

    def __init__(self, width, height):
        self.cluster    = {}
        self.color      = {}
        self.last_label = 0
        self.label      = np.zeros((width, height), dtype=np.ndarray)
        self.selected   = []
        self.parametrization = {}

    def print(self):
        for label, coords in self.cluster.items():
            print(label, coords)

    def describe(self):
        for label, coords in self.cluster.items():
            print(label, len(coords))

    def describe_selected(self):
        if self.selected:
            for label in self.selected:
                coords = self.cluster[label]
                print(label, f"number of pixels: {len(coords)}     center: {find_center(coords)}")
        else:
            print("no clusters selected")

    def new_cluster(self, x: int, y: int, pixel_color: int | None = None):
        self.last_label += 1
        self.label[x, y] = self.last_label
        self.cluster[self.last_label] = [(x, y)]
        if pixel_color: self.color[self.last_label] = pixel_color

    def add_to_existing(self, x: int, y: int, x_old: int, y_old: int):
        label_old = self.label[x_old, y_old]
        label_new = self.label[x, y]
        if label_old == label_new: return
        if label_new == 0:  # this is a new cluster
            self.label[x, y] = label_old
            self.cluster[label_old].append((x, y))
        else:  # this is a merge
            for (x, y) in self.cluster[label_new]:
                self.label[x, y] = label_old
            self.cluster[label_old].extend(self.cluster[label_new])
            del self.cluster[label_new]
        return


def extrude_hull(hull: np.ndarray, border_thickness) -> np.ndarray:
    if border_thickness == 0: return hull
    new_hull = np.zeros(hull.shape)
    x_range = range(hull.shape[1])
    y_range = range(hull.shape[0])
    min_remaining_span = abs(1.1*border_thickness)
    for j in y_range:
        nonzero_i_list = list(filter(lambda ii: hull[j, ii] > 0, x_range))
        if len(nonzero_i_list) < min_remaining_span: continue

        min_i = min(nonzero_i_list)
        max_i = max(nonzero_i_list)
        for i in range(min_i + border_thickness, max_i - border_thickness):
            new_hull[j, i] = 255
    return new_hull


def black_clusters(x: int, y: int, x_old_range: range, y_old_range: range, pixel: np.ndarray,
                   clust_book: ClusterBookkeeping, cutoff_lower: float = -1, cutoff_upper: float = 10):

    if pixel[x, y] < cutoff_lower: return
    if pixel[x, y] > cutoff_upper: return  # we are looking for black pixels - this is specific for this problem
    for x_old in x_old_range:
        for y_old in y_old_range:
            if clust_book.label[x_old, y_old] == 0: continue  # this one does not belong to any cluster
            clust_book.add_to_existing(x, y, x_old, y_old)

    if clust_book.label[x, y] == 0:  # are the pixels to the left or above me already marked as belonging to a cluster?
        # we might be duplicating some work here, but this presumably won't be the bottleneck
        if x > 0 and clust_book.label[x - 1, y] > 0:
            clust_book.add_to_existing(x, y, x - 1, y)
        elif y > 0 and clust_book.label[x, y - 1] > 0:
            clust_book.add_to_existing(x, y, x, y - 1)

    if clust_book.label[x, y] == 0:  # new cluster
        clust_book.new_cluster(x, y)

    return


def black_and_white_clusters(x: int, y: int, x_old_range: range, y_old_range: range, pixel: np.ndarray,
                             clust_book: ClusterBookkeeping, cutoff_lower: float = -1, cutoff_upper: float = 10):

    if cutoff_lower < pixel[x, y] < cutoff_upper: return
    pixel_color = BLACK if pixel[x, y] <= cutoff_lower else WHITE

    # are the pixels to the left or above me already marked as belonging to a cluster?
    for x_old in x_old_range:
        for y_old in y_old_range:
            label = clust_book.label[x_old, y_old]
            if label == 0: continue  # pixel at [x_old, y_old] does not belong to any cluster
            if clust_book.color[label] != pixel_color: continue
            clust_book.add_to_existing(x, y, x_old, y_old)

    if clust_book.label[x, y] == UNASSIGNED:
        # we are growing in one direction only
        if x > 0 and (label := clust_book.label[x - 1, y]) > 0:
            if clust_book.color[label] == pixel_color:
                clust_book.add_to_existing(x, y, x - 1, y)
        elif y > 0 and (label := clust_book.label[x, y - 1]) > 0:
            if clust_book.color[label] == pixel_color:
                clust_book.add_to_existing(x, y, x, y - 1)

    if clust_book.label[x, y] == UNASSIGNED:  # start new cluster
        clust_book.new_cluster(x, y, pixel_color)

    return


def place_pixel(x: int, y: int, x_old_range: range, y_old_range: range, pixel: np.ndarray,
                clusters: ClusterBookkeeping, cutoffs: tuple = (-1, 10),
                clustering_criterion: str = "black"):

    (cutoff_lower, cutoff_upper) = cutoffs
    if clustering_criterion == "black":
        black_clusters(x, y, x_old_range, y_old_range, pixel, clusters, cutoff_lower, cutoff_upper)
    elif clustering_criterion == "black and white":
        black_and_white_clusters(x, y, x_old_range, y_old_range, pixel, clusters, cutoff_lower, cutoff_upper)
    else:
        raise Exception(f"unrecognized clustering criterion: {clustering_criterion}")

    return


def find_clusters(pixel_array: np.ndarray, mask: np.ndarray, cutoffs: tuple = (10, 100)) -> ClusterBookkeeping:
    x_range = pixel_array.shape[0]
    y_range = pixel_array.shape[1]

    (min_value, max_value) = (np.amin(pixel_array), np.amax(pixel_array))
    # when we are looking for cluster in the vasculatre surrounding a disc candidate,
    # the matrix is boolean (numpy.bool_, to make things worse), so the cutoff does not apply
    if f"{max_value}".isnumeric() and cutoffs[0] >= max_value:
        print(isinstance(max_value, bool), type(max_value))
        scream(f"this is not going to work:  cutoff is {cutoffs[0]} and the range is  {min_value}  - {max_value}")
        exit(1)

    # for all pixels along the new front
    # if one of the max 3  neighbors  along the generic front are within some cluster, join
    # otherwise start new cluster
    clusters = ClusterBookkeeping(x_range, y_range)

    new_front_x = 1
    new_front_y = 1
    while new_front_x < x_range or new_front_y < y_range:
        # in the case of rectangle we might be able to advance in one direction only
        if new_front_x >= x_range: new_front_x = x_range - 1
        if new_front_y >= y_range: new_front_y = y_range - 1

        # along the x axis
        y = new_front_y
        y_old_range = range(new_front_y-1, new_front_y)  # note this is range only formally
        for x in range(new_front_x):
            x_old_range = range(max(x-1, 0), min(x+2, new_front_y))
            if mask is not None and not mask[x, y]: continue
            place_pixel(x, y, x_old_range, y_old_range, pixel_array, clusters, cutoffs,
                        clustering_criterion="black")
        # print("----")
        # down the y axis
        x = new_front_x
        x_old_range = range(new_front_x-1, new_front_x)
        for y in range(new_front_y):
            y_old_range =  range(max(y-1, 0), min(y+2, new_front_x))
            if mask is not None and not mask[x, y]: continue
            place_pixel(x, y, x_old_range, y_old_range, pixel_array, clusters, cutoffs,
                        clustering_criterion="black")
        # print("----")

        # corner
        x = new_front_x
        x_old_range = range(new_front_x-1, new_front_x)
        y = new_front_y
        y_old_range = range(new_front_y-1, new_front_y)  # note this is range only formally
        if mask is not None and mask[x, y]:
            place_pixel(x, y, x_old_range, y_old_range, pixel_array, clusters, cutoffs,
                        clustering_criterion="black")

        # advance the front
        new_front_x += 1
        new_front_y += 1

        # if new_front_x % 1000 == 0 and new_front_x < x_range:
        #     print("*************  %6d  %6d " % (new_front_x, new_front_y))
    return clusters


def principal_axes(cluster: IntPointList, do_subsampling=True, verbose=False) -> list[float]:
    # subsample

    subsample = sample(cluster, min(1000, len(cluster))) if do_subsampling else cluster

    subsize = len(subsample)
    # find cm
    x_cm = sum([x for (x, y) in subsample]) / subsize
    y_cm = sum([y for (x, y) in subsample]) / subsize
    x_recentered = [x - x_cm for (x, y) in subsample]
    y_recentered = [y - y_cm for (x, y) in subsample]
    # remove outlayers - in an attempt to get rid of eyelashes and blood vessels that appear to stick out
    # [x_shaved, y_shaved] = shave(x_recentered, y_recentered)

    # find moments of inertia
    I_xx = sum([x * x for x in x_recentered])
    I_yy = sum([y * y for y in y_recentered])
    if abs(I_yy - I_xx) < 0.1: return [I_xx, I_yy]

    I_xy = sum([x * y for (x, y) in zip(x_recentered, y_recentered)])
    theta = atan(2 * I_xy / (I_yy - I_xx)) / 2

    # moments of inertia about the principal axes
    # https://www.ae.msstate.edu/vlsm/shape/area_moments_of_inertia/papmi.htm
    I_xx_principal = I_xx * cos(theta) ** 2 + I_yy * sin(theta) ** 2 - I_xy * sin(2 * theta)
    I_yy_principal = I_xx * sin(theta) ** 2 + I_yy * cos(theta) ** 2 + I_xy * sin(2 * theta)
    return [I_xx_principal, I_yy_principal]


def bigger_to_smaller_ratio(I_xx_principal, I_yy_principal, verbose=False) -> float:
    ratio = I_xx_principal / I_yy_principal
    if verbose: print(f"\tprincipal axes ratio: {ratio:.2f},   inverse {1/ratio:.2f}")
    if ratio == 0: print("oink") and exit(1)
    # if the moments of inertia are comparable it's a circle
    return ratio if ratio >= 1.0 else 1.0/ratio


def principal_axes_ratio(cluster: IntPointList, verbose=False) -> float:
    # subsample
    [I_xx_principal, I_yy_principal] = principal_axes(cluster, verbose)
    return bigger_to_smaller_ratio(I_xx_principal, I_yy_principal, verbose)


def find_circle_like_within_mask(image_in: np.ndarray, mask: np.ndarray,
                                 disc_asym_cutoff, pix_int_upper_cutoff, verbose) -> ClusterBookkeeping | None:

    # these are RGB images, so in principle this number should go 0-255
    clusters = find_clusters(image_in, mask, cutoffs=(10, pix_int_upper_cutoff))
    if verbose:
        print(f"found {len(clusters.cluster)} clusters within the mask")
    if len(clusters.cluster) == 0:
        return None

    # sort cluster labels by cluster size in pixels
    sorted_labels = list(sorted(clusters.cluster.keys(), key=lambda k: len(clusters.cluster[k]), reverse=True))

    # from all clusters findd those that are most circle-like
    axes_ratio = {}  # axes ratio, for labels that are cicle like
    min_cluster = 500 # 1*1e3
    max_cluster = 10*1e3
    for label in sorted_labels:
        if len(clusters.cluster[label]) < min_cluster or len(clusters.cluster[label]) > max_cluster: continue
        ar = principal_axes_ratio(clusters.cluster[label], verbose=False)
        # the moments of inertia go as the 4th power of radius for a disc: pi*r^4/4
        ratio = pow(ar, 0.25)
        if verbose:
            clustsize = len(clusters.cluster[label])
            print(f"\tcluster {label}: size {clustsize}  ratio {ratio: 0.3f}  ")
        if ratio < disc_asym_cutoff:  # and cness < cness_cutoff:
            axes_ratio[label] = ratio

    if verbose: print(f"number of circle-like clusters: {len(axes_ratio)}")
    clusters.selected = sorted(axes_ratio.keys(), key=lambda l: axes_ratio[l])
    return clusters


def find_center(list_of_coords) -> list[int]:
    if len(list_of_coords) == 0: return [0, 0]
    x_center = int(round(sum([x for (x, y) in list_of_coords])/len(list_of_coords), 0))
    y_center = int(round(sum([y for (x, y) in list_of_coords])/len(list_of_coords), 0))

    return [x_center, y_center]


def dist(a, b) -> float:
    return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def distance_to_the_furthest_point(list_of_coords, center) -> float:
    return max([dist(coords, center) for coords in list_of_coords])



def pointlist2ndarray(point_list: IntPointList, shape) -> np.ndarray:
    bw_image = np.zeros(shape, dtype=np.ndarray)
    for row, column in point_list:
        if column < 0: continue
        if row < 0: continue
        try:
            bw_image[row, column] = 1
        except Exception as e:
            print(e)
            print(f"row type", type(row))
            print(f"column type", type(column))
            exit()
    return bw_image

def content_range(img: np.ndarray, direction: int, verbose=False) -> int:
    # direction 0 = y
    # direction 1 = x
    row_means = np.mean(img, axis=direction)
    center = np.argmax(row_means)

    # Get intensity profile along that row
    if direction == 0:
        profile = img[:, center]
    elif direction == 1:
        profile = img[center, :]
    else:
        raise Exception(f"direction {direction} is not supported")

    threshold = (profile.min() + 1)*1.2 # for the cases where black is off black
    # Find where profile exceeds the threshold
    edge_indices = np.where(profile > threshold)[0]
    if len(edge_indices) == 0:
        raise Exception(f"No edge indices  detected. Try adjusting the threshold.")

    # Find left and right edges
    start_edge = edge_indices[0]
    end_edge = edge_indices[-1]

    # Calculate radius and center
    distance = int(end_edge - start_edge)
    if verbose:
        print(f"Circle detected (1D method):")
        print(f"  Scan direction: {'x' if direction == 1 else 'y'}")
        print(f"  Start edge: {start_edge}")
        print(f"  End edge: {end_edge}")
        print(f"  Radius: {distance} pixels")

    return distance



def disc_and_fovea_detector(original_image_path: Path, usable_region_path:  Path | None,
                            eye: str, path_to_image_out, verbose=True) -> tuple[tuple, tuple] | None:

    original_image  = gray_read_blur(str(original_image_path))
    if usable_region_path is not None:
        mask = rgba_255_path_to_255_ndarray(usable_region_path, channel=2)
    else:
        # use an elliptical mask to reduce the search area
        # find roughly where the boundaries of the actual image are
        x_range = content_range(original_image, 1, verbose=False)
        y_range = content_range(original_image, 0, verbose=False)
        height, width = original_image.shape
        mask =  elliptical_mask(height, width, radius_x=x_range//8, radius_y=y_range//8)
        # ndarray_boolean_to_255_png(mask, path_to_image_out)
        # print(f"wrote mask to {path_to_image_out}")
        # exit()
    h, w = mask.shape
    center_y, center_x = h // 2, w // 2

    cluster_candidates = []
    assym_ratio_cutoffs = (2.5, 3.0)
    pixel_intensity_cutoffs  = (50, 70, 90, 110)

    for disc_asym, pix_int_upper_cutoff  in product(assym_ratio_cutoffs, pixel_intensity_cutoffs):
        if verbose: print(f"*** params scan:  asym_cutoff {disc_asym}   pix int upper cutoff {pix_int_upper_cutoff} ")
        cluster_book = find_circle_like_within_mask(original_image, mask, disc_asym, pix_int_upper_cutoff, verbose=verbose)
        if cluster_book is None:
            if verbose: print(f"no clusters found")
            continue

        if verbose:
            print(f"found {len(cluster_book.selected)} circle-ish clusters ", end="")
            print(f"at asym_cutoff {disc_asym}  pixel_intensity_cutoff {pix_int_upper_cutoff} ")
            print()
        if len(cluster_book.selected) < 2: continue
        cluster_book.parametrization = {"disc_asym": disc_asym, "pix_int": pix_int_upper_cutoff}
        cluster_candidates.append(cluster_book)
        break

    if len(cluster_candidates) == 0:
        print(f"no disc + fovea found for {original_image_path}")
        return None

    cluster_centers = []
    for cluster_data in cluster_candidates:
        cluster_as_nd_array = []
        dist_to_img_center = []
        cluster_data: ClusterBookkeeping
        for label in cluster_data.selected[:2]:
            coords = cluster_data.cluster[label]
            cluster_center = find_center(coords)
            cluster_centers.append(tuple(cluster_center))
            dist_to_img_center.append(dist(cluster_center, (center_y, center_x)))
            # print(label, f"number of pixels: {len(coords)}   center: {cluster_center}   dist: {dist_to_img_cetner}")
            cluster_as_nd_array.append(pointlist2ndarray(coords, original_image.shape))
        # i += 1
        outnm = str(path_to_image_out) # .replace(".png", f".{i}.png")
        # red should be the ONH, green the fovea
        if dist_to_img_center[1] > dist_to_img_center[0]:
            channel_visualization(cluster_as_nd_array[0],  cluster_as_nd_array[1], None, outnm, alpha=True)
            disc_center, fovea_center = cluster_centers[:2]
        else:
            channel_visualization(cluster_as_nd_array[1],  cluster_as_nd_array[0], None, outnm, alpha=True)
            fovea_center, disc_center = cluster_centers[:2]

        print(f"clusters written to {outnm}")
        return disc_center, fovea_center

    return None

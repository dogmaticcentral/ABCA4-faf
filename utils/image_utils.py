_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

from itertools import product
from pathlib import Path

import cairosvg
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image as PilImage
from PIL import ImageFilter, ImageOps
from skimage import filters, morphology
from skimage.io import imread, imsave
from skimage.util import img_as_ubyte


def channel_visualization(r_channel: np.ndarray, g_channel: np.ndarray, b_channel: np.ndarray,
                          outname: str, alpha: bool = False):

    if g_channel.shape != r_channel.shape or b_channel.shape != r_channel.shape:
        print("all image arrays must be of the same shape for the channel hack to work")
        exit(1)
    nr, nc = r_channel.shape

    image_array = np.zeros((nr, nc, 4 if alpha else 3))
    image_array[..., 0] = np.divide(r_channel,  np.amax(r_channel)) if np.amax(r_channel) > 0 else 0
    image_array[..., 1] = np.divide(g_channel,  np.amax(g_channel)) if np.amax(g_channel) > 0 else 0
    image_array[..., 2] = np.divide(b_channel,  np.amax(b_channel)) if np.amax(b_channel) > 0 else 0
    if alpha:
        for r in range(nr):
            for c in range(nc):
                if sum(image_array[r, c][0:3]) > 0:
                    image_array[r, c][3]  = 1
    plt.imsave(outname, image_array)


def from_gray(gray_img: np.ndarray, channel=2) -> np.ndarray:
    y_max, x_max = gray_img.shape[:2]
    color_arr = np.zeros((y_max, x_max, 4))
    for y, x  in product(range(y_max), range(x_max)):
        if gray_img[y, x] == 0: continue
        color_arr[y, x, 3] = 255
        color_arr[y, x, channel] = gray_img[y, x]
    return color_arr


def get_image_dimensions(file_path):
    with PilImage.open(file_path) as img:
        return img.size  # returns (width, height)


def gray_read_blur(path: str) -> np.ndarray:
    rgba_image = PilImage.open(path).filter(ImageFilter.GaussianBlur(radius=10))
    return np.array(ImageOps.grayscale(rgba_image))


def grayscale_img_path_to_255_ndarray(img_path) -> np.ndarray:
    img_as_array: np.ndarray = imread(str(img_path), as_gray=True)
    if np.max(img_as_array) < 1.1:
        return img_as_ubyte(img_as_array)
    else:
        return img_as_array


def ndarray_to_int_png(ndarray: np.ndarray, outpng: Path | str):
    imsave(outpng, ndarray.astype(np.uint8))


def ndarray_boolean_to_255_png(ndarray: np.ndarray, outpng: Path | str):
    new_array = np.zeros(ndarray.shape)
    (height, width) = ndarray.shape
    for row, col in product(range(height), range(width)):
        if not ndarray[row, col]: continue
        new_array[row, col] = 255

    imsave(outpng, new_array.astype(np.uint8))


def ndarray_to_4channel_png(ndarray: np.ndarray,  outpng: Path | str):
    imsave(outpng, ndarray.astype(np.uint8))


def pil_image_to_grayscale_png(pil_image: PilImage, outpng: Path | str):
    PilImage.fromarray(pil_image).save(str(outpng))


def rgba_255_path_to_255_ndarray(img_path: Path | str, channel: int = 0) -> np.ndarray:
    """ Inputs filepath to a 255  image and returns a single channel as ndarray.
    :param simple_object_img_path: Path | str
    :param channel: int
    :return: numpy.ndarray
    """
    simple_object_img_path = str(img_path)
    # mask as a line
    # the way inkscape saves transparent points is [255, 255, 255, 0],
    # which makes turning to grayscale somewhat nontrivial
    # i.e., this will not work:  [:, :, 2] # keep only the blue channel
    return to_gray(imread(simple_object_img_path), channel=channel)


def rgba_255_path_to_255_outline_ndarray(simple_object_img_path: Path | str, channel: int = 0) -> np.ndarray:
    """ Inputs filepath to a simple object (e.g polygone) stored in one channel of rgba image adn returns ti as ndarray.
        It may work for complicated objects, but this is untested.
    :param simple_object_img_path: Path | str
    :param channel: int
    :return: numpy.ndarray
    """
    simple_object_img_path = str(simple_object_img_path)
    # mask as a line
    # the way inkscape saves transparent points is [255, 255, 255, 0],
    # which makes turning to grayscale somewhat nontrivial
    # i.e., this will not work:  [:, :, 2] # keep only the blue channel
    input_as_ndarray: np.ndarray = to_gray(imread(simple_object_img_path), channel=channel)
    outline_gray = filters.sobel(input_as_ndarray.astype(float)).astype(np.uint8)
    outline_gray_thicker = morphology.dilation(outline_gray, footprint=morphology.disk(12))
    return outline_gray_thicker


def svg2png(svg_filepath: Path | str, png_filepath: Path | str):
    cairosvg.svg2png(url=str(svg_filepath), write_to=str(png_filepath))


def to_gray(color_img: np.ndarray, channel=2) -> np.ndarray:
    y_max, x_max = color_img.shape[:2]
    alpha  = color_img.shape[2] == 4
    gray_arr = np.zeros((y_max, x_max))
    for y, x  in product(range(y_max), range(x_max)):
        if alpha and color_img[y, x, 3] == 0: continue
        if color_img[y, x, channel] > 0:
            gray_arr[y, x] = color_img[y, x, channel]
    return gray_arr

_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

import numpy as np
from PIL import Image as PilImage  # scikit image object is also called Image

from utils.ndarray_utils import extremize


def extremize_pil(input_pil_image: PilImage,  cutoff=230, invert=False):

    pixelmat = np.asarray(input_pil_image)
    return extremize(pixelmat, cutoff, invert)

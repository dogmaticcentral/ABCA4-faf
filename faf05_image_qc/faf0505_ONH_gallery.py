#!/usr/bin/env python3
"""
Image Gallery Generator

Extracts red-masked regions from TIFF images paired with PNG masks,
and creates a 5x5 gallery of the extracted samples.
"""

import sys
from typing import Optional

import numpy as np

from faf05_image_qc.qc_utils.gallery import parse_args, make_gallery



def extract_red_masked_region_plain(
        tiff_array: np.ndarray,
        png_array: np.ndarray
) -> Optional[np.ndarray]:
    """
    Extract pixels from TIFF where PNG has pure red (255, 0, 0).

    Args:
        tiff_array: Grayscale TIFF image as numpy array
        png_array: RGB PNG image as numpy array

    Returns:
        Minimal bounding array of extracted pixels, or None if no red found
    """
    # Create mask for pure red pixels (R=255, G=0, B=0)
    red_mask = (
            (png_array[:, :, 0] == 255) &
            (png_array[:, :, 1] == 0) &
            (png_array[:, :, 2] == 0)
    )

    if not red_mask.any():
        return None

    # Find bounding box of red pixels
    rows = np.any(red_mask, axis=1)
    cols = np.any(red_mask, axis=0)
    row_min, row_max = np.where(rows)[0][[0, -1]]
    col_min, col_max = np.where(cols)[0][[0, -1]]
    # print(f"**{row_max-row_min}, {col_max-col_min}")

    # Extract minimal region
    extracted = tiff_array[row_min:row_max + 1, col_min:col_max + 1].copy()

    return extracted



def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_args()
    make_gallery(args, 'disc_and_macula', extract_red_masked_region_plain)

if __name__ == "__main__":
    sys.exit(main())

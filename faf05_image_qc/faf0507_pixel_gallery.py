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



def extract_pixels_from_blue_masked_region(
        tiff_array: np.ndarray,
        png_array: np.ndarray
) -> Optional[np.ndarray]:
    """
    Extract a 20x20 pixel region from the center of the blue mask area from TIFF.

    Args:
        tiff_array: Grayscale TIFF image as numpy array
        png_array: RGB PNG image as numpy array

    Returns:
        20x20 array extracted from center of blue region, padded with black if needed, or None if no blue found
    """
    # Create mask for pure blue pixels (R=0, G=0, B=255)
    blue_mask = (
            (png_array[:, :, 0] == 0) &
            (png_array[:, :, 1] == 0) &
            (png_array[:, :, 2] == 255)
    )

    if not blue_mask.any():
        print("no blue pixels")
        exit()

    # Find center of blue region
    rows = np.any(blue_mask, axis=1)
    cols = np.any(blue_mask, axis=0)
    row_indices = np.where(rows)[0]
    col_indices = np.where(cols)[0]

    center_row = (row_indices[0] + row_indices[-1]) // 2
    center_col = (col_indices[0] + col_indices[-1]) // 2

    # Calculate nxn region boundaries centered at the blue mask center
    n = 10
    half_size = n // 2
    row_start = center_row - half_size
    row_end = center_row + half_size
    col_start = center_col - half_size
    col_end = center_col + half_size

    # Create 20x20 array filled with black (zeros)
    extracted = np.zeros((n, n), dtype=tiff_array.dtype)

    # Calculate valid region boundaries within the image
    valid_row_start = max(0, row_start)
    valid_row_end = min(tiff_array.shape[0], row_end)
    valid_col_start = max(0, col_start)
    valid_col_end = min(tiff_array.shape[1], col_end)

    # Calculate corresponding indices in the extracted array
    extracted_row_start = valid_row_start - row_start
    extracted_row_end = extracted_row_start + (valid_row_end - valid_row_start)
    extracted_col_start = valid_col_start - col_start
    extracted_col_end = extracted_col_start + (valid_col_end - valid_col_start)

    # Copy the valid region from tiff_array
    extracted[extracted_row_start:extracted_row_end, extracted_col_start:extracted_col_end] = \
        tiff_array[valid_row_start:valid_row_end, valid_col_start:valid_col_end]

    return extracted


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_args()
    mask_file_extension = 'bg_sample'
    # mask_file_extension = 'auto_bg'  # for controls, I have more of those
    make_gallery(args, mask_file_extension, extract_pixels_from_blue_masked_region)

if __name__ == "__main__":
    sys.exit(main())

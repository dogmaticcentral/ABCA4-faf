#!/usr/bin/env python3
"""
Extract TIFF image metadata using tiffinfo command.

This script recursively finds all TIFF files in a directory and extracts
their width, height, and rows/strip information using the tiffinfo command.
"""
import imquality.brisque as brisque
import subprocess
import sys
from pathlib import Path
from typing import Optional
import cv2
from brisque import BRISQUE

from faf05_image_qc.qc_utils.stat_utils import gradient_by_mod8_x, outliers


def run_tiffinfo(tiff_path: Path) -> Optional[dict[str, str]]:
    """
    Run tiffinfo command on a TIFF file and extract metadata.

    Args:
        tiff_path: Path to the TIFF file

    Returns:
        Dictionary with 'width', 'length', and 'rows_strip' keys, or None if extraction fails
    """
    try:
        result = subprocess.run(
            ['tiffinfo', str(tiff_path)],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout
        width = length = rows_strip = None

        for line in output.splitlines():
            line = line.strip()
            if 'Image Width:' in line:
                parts = line.split()
                width = parts[2]
                if 'Image Length:' in line:
                    length = parts[5]
            elif 'Rows/Strip:' in line:
                rows_strip = line.split(':')[1].strip()

        if width and length and rows_strip:
            return {
                'width': width,
                'length': length,
                'rows_strip': rows_strip
            }

    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        print("Error: tiffinfo command not found. Please install libtiff-tools.", file=sys.stderr)
        sys.exit(1)

    return None

def brisque_score(tiff_file):
    # the images have big black background, so score only 1/4 in the center
    img_gray = cv2.imread(tiff_file, cv2.IMREAD_GRAYSCALE)
    img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

    # Get image dimensions
    height, width = img_rgb.shape[:2]

    # Calculate crop boundaries (centered, half width and half height)
    x_start = width // 4
    x_end = 3 * width // 4
    y_start = height // 4
    y_end = 3 * height // 4

    # Crop the image
    img_rgb_cropped = img_rgb[y_start:y_end, x_start:x_end]

    obj = BRISQUE(url=False)
    bscore = obj.score(img=img_rgb_cropped)
    return bscore

def process_directory(directory: str) -> None:
    """
    Process all TIFF files in directory and subdirectories.

    Args:
        directory: Path to the directory to search
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Print header
    print("image_path\twidth\tlength\trows/strip\tbrisque score\tgrad outliers")

    # Find all TIFF files
    tiff_patterns = ['*.tiff', '*.tif', '*.TIFF', '*.TIF']
    outfnm = f"{Path(directory).name}_tiffinfo.tsv"
    outf = open(outfnm, 'w')
    for pattern in tiff_patterns:
        for tiff_file in dir_path.rglob(pattern):
            info = run_tiffinfo(tiff_file)
            if info:
                bscore =  brisque_score(tiff_file)
                results = gradient_by_mod8_x(tiff_file)
                outls = outliers(results)
                outln = f"{tiff_file}\t{info['width']}\t{info['length']}\t{info['rows_strip']}\t{bscore:.1f}\t{outls}"
                print(outln)
                print(outln, file=outf)
    outf.close()

def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <directory_path>", file=sys.stderr)
        sys.exit(1)

    directory = sys.argv[1]
    process_directory(directory)


if __name__ == "__main__":
    main()

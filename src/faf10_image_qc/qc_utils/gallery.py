import argparse
import logging
import random
from pathlib import Path
from typing import Tuple, Callable, Optional

import numpy as np
from PIL import Image


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract red-masked image regions and create a gallery"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Root directory to search recursively for image pairs"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("gallery.png"),
        help="Output gallery filename (default: gallery.png)"
    )
    parser.add_argument(
        "-n", "--num-pairs",
        type=int,
        default=25,
        help="Number of pairs to select (default: 25)"
    )
    parser.add_argument(
        "-c", "--cell-size",
        type=int,
        default=100,
        help="Size of each gallery cell in pixels (default: 100)"
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    if not args.directory.is_dir():
        logger.error(f"Directory not found: {args.directory}")
        return 1

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    return args


def find_image_pairs(directory: Path, mask_file_extension: str) -> list[Tuple[Path, Path]]:
    """
    Find pairs of TIFF and PNG files in the same directories recursively.

    Searches for files matching <name_root>.tiff and <name_root>.disc_and_macula.png
    in the same directory.

    Args:
        directory: Root directory to search recursively
        mask_file_extension: File extension of PNG masks

    Returns:
        List of tuples (tiff_path, png_path)
    """
    if not mask_file_extension:
        raise ValueError("mask_file_extension must be specified")

    pairs = []

    # Iterate through all subdirectories
    for subdir in [directory] + list(directory.rglob("*")):
        if not subdir.is_dir():
            continue

        # Find TIFF files in this directory
        tiff_files = {f.stem: f for f in subdir.glob("*.tiff")}

        # Find PNG files in this directory
        png_files = {}
        for f in subdir.glob(f"*.{mask_file_extension}.png"):
            # Extract name_root by removing the ".disc_and_macula" suffix
            name_root = f.name.replace(f".{mask_file_extension}.png", "")
            png_files[name_root] = f

        # Find matching pairs
        for name_root in tiff_files:
            if name_root in png_files:
                pairs.append((tiff_files[name_root], png_files[name_root]))

    logger.info(f"Found {len(pairs)} image pairs")
    return pairs


def validate_image_dimensions(tiff_path: Path, png_path: Path) -> bool:
    """
    Verify that TIFF and PNG have identical dimensions.

    Args:
        tiff_path: Path to TIFF file
        png_path: Path to PNG file

    Returns:
        True if dimensions match, False otherwise
    """
    try:
        tiff_img = Image.open(tiff_path)
        png_img = Image.open(png_path)

        if tiff_img.size != png_img.size:
            logger.warning(
                f"Dimension mismatch for {tiff_path.stem}: "
                f"TIFF {tiff_img.size} vs PNG {png_img.size}"
            )
            return False
        return True
    except Exception as e:
        logger.warning(f"Error validating {tiff_path.stem}: {e}")
        return False


def filter_valid_pairs(pairs: list[Tuple[Path, Path]]) -> list[Tuple[Path, Path]]:
    """
    Filter pairs to keep only those with matching dimensions.

    Args:
        pairs: List of image pair tuples

    Returns:
        Filtered list with only valid pairs
    """
    valid_pairs = [
        pair for pair in pairs
        if validate_image_dimensions(pair[0], pair[1])
    ]

    logger.info(f"Valid pairs after dimension check: {len(valid_pairs)}")
    return valid_pairs


def read_image_pair(
        tiff_path: Path,
        png_path: Path
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Read TIFF as grayscale and PNG as RGB.

    Args:
        tiff_path: Path to TIFF file
        png_path: Path to PNG file

    Returns:
        Tuple of (grayscale_array, rgb_array)
    """
    tiff_img = Image.open(tiff_path).convert("L")
    png_img = Image.open(png_path).convert("RGB")

    return np.array(tiff_img), np.array(png_img)


def process_image_pairs(
    pairs: list[Tuple[Path, Path]],
    callback: Callable[[np.ndarray, np.ndarray], np.ndarray | None]
) -> list[np.ndarray]:
    """
    Process image pairs using a provided callback function.

    Args:
        pairs: List of image pair tuples
        callback: Function to apply to each image pair

    Returns:
        List of processed sample arrays
    """
    samples = []

    for tiff_path, png_path in pairs:
        try:
            print(f"reading {tiff_path} {png_path}")
            tiff_array, png_array = read_image_pair(tiff_path, png_path)
            extracted = callback(tiff_array, png_array)
            if extracted is None:
                logger.warning(f"In process_image_pairs(): No valid data found in {tiff_path.stem}")
            else:
                samples.append(extracted)

        except Exception as e:
            logger.error(f"Error processing {tiff_path.stem}: {e}")

    logger.info(f"Successfully processed {len(samples)} samples")
    return samples


def create_gallery(
        samples: list[np.ndarray],
        cell_size: Tuple[int, int] = (100, 100),
        gallery_shape: Tuple[int, int] = (5, 5)
) -> Optional[np.ndarray]:
    """
    Create a gallery matrix from extracted samples, resized to fit cells,
    with thin black lines between individual cells.

    Args:
        samples: List of extracted image arrays (assumed grayscale)
        cell_size: Size to resize each sample to (height, width)
        gallery_shape: Shape of gallery grid (rows, cols)

    Returns:
        Gallery image as numpy array with grid lines, or None if no samples
    """
    if not samples:
        logger.error("No samples provided for gallery")
        return None

    rows, cols = gallery_shape
    total_slots = rows * cols
    cell_height, cell_width = cell_size

    if len(samples) < total_slots:
        logger.warning(
            f"Only {len(samples)} samples for {total_slots} gallery slots. "
            f"Using available samples."
        )

    # Define border (grid line) thickness
    border_thickness = 1  # pixels

    # Compute total size with borders
    gallery_height = rows * cell_height + (rows - 1) * border_thickness
    gallery_width = cols * cell_width + (cols - 1) * border_thickness

    # Create gallery canvas (initialized to black)
    gallery = np.zeros((gallery_height, gallery_width), dtype=np.uint8)

    # Place samples into gallery cells
    for idx, sample in enumerate(samples):
        if idx >= total_slots:
            break

        row_idx = idx // cols
        col_idx = idx % cols
        # Compute position with borders
        y = row_idx * (cell_height + border_thickness)
        x = col_idx * (cell_width + border_thickness)

        # Resize sample
        sample_img = Image.fromarray(sample, mode="L")
        sample_img = sample_img.resize((cell_width, cell_height), Image.Resampling.BOX)
        resized_sample = np.array(sample_img)

        # Insert into gallery
        gallery[y:y + cell_height, x:x + cell_width] = resized_sample

    return gallery


def save_gallery(
        gallery: np.ndarray,
        output_path: Path
) -> None:
    """
    Save gallery as grayscale image.

    Args:
        gallery: Gallery numpy array
        output_path: Path where to save the image
    """
    img = Image.fromarray(gallery, mode="L")
    img.save(output_path)
    logger.info(f"Gallery saved to {output_path}")


def make_gallery(args: argparse.Namespace, mask_file_extension: str,
                 extract_masked_region: Callable[[np.ndarray, np.ndarray], np.ndarray | None]) -> None:

    if not mask_file_extension:
        raise Exception("No mask file extension provided")

    try:
        # Find and filter pairs
        pairs = find_image_pairs(args.directory, mask_file_extension)
        valid_pairs = filter_valid_pairs(pairs)

        if not valid_pairs:
            logger.error("No valid image pairs found")
            return 1

        # Select random pairs
        num_to_select = min(args.num_pairs, len(valid_pairs))
        selected_pairs = random.sample(valid_pairs, num_to_select)
        logger.info(f"Selected {num_to_select} random pairs")
        # Place samples into gallery cells
        for idx, sp in enumerate(selected_pairs):
            if idx >= 25:
                break
            row_idx = idx // 5
            col_idx = idx % 5

        # Process pairs and create gallery
        samples = process_image_pairs(selected_pairs, extract_masked_region)

        if not samples:
            logger.error("No samples could be extracted")
            return 1

        gallery = create_gallery(
            samples,
            cell_size=(args.cell_size, args.cell_size)
        )

        if gallery is None:
            logger.error("Failed to create gallery")
            return 1

        save_gallery(gallery, args.output)
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

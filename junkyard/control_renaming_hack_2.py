#!/usr/bin/env python3
"""Reorganize Control image files into a hierarchical directory structure."""

import argparse
import re
from pathlib import Path
from typing import List, Tuple


def normalize_filename(filename: str) -> str:
    """Convert .tif to .tiff and collapse multiple spaces to single underscore."""
    # Replace consecutive spaces with single underscore
    name = re.sub(r' +', '_', filename)
    # Change .tif to .tiff
    name = re.sub(r'\.tif$', '.tiff', name, flags=re.IGNORECASE)
    return name


def convert_double_letter(name: str) -> str:
    """Convert AA, AB, etc. to lowercase a, b, etc."""
    # Match pattern like Control_AA, Control_AB, etc.
    match = re.search(r'Control_([A-Z]{2})_', name)
    if match:
        double = match.group(1)
        # AA->a, AB->b, AC->c, etc.
        index = (ord(double[0]) - ord('A')) * 26 + (ord(double[1]) - ord('A'))
        single = chr(ord('a') + index)
        name = name.replace(f'Control_{double}_', f'Control_{single}_')
    return name


def parse_filename(filename: str) -> Tuple[str, str, str]:
    """Extract subject ID, eye (OD/OS), and remainder from filename."""
    # Pattern: Control_X_OD/OS_remainder
    match = re.match(r'Control_([A-Za-z]+)_(OD|OS)_(.+)\.tiff$', filename)
    if not match:
        raise ValueError(f"Cannot parse filename: {filename}")
    return match.groups()


def process_files(source_dir: Path, dry_run: bool = False) -> None:
    """Process all .tif files in the source directory."""
    tif_files = list(source_dir.glob('*.tif'))

    if not tif_files:
        print("No .tif files found")
        return

    print(f"Found {len(tif_files)} files")
    if dry_run:
        print("DRY RUN - no files will be moved\n")

    for file_path in tif_files:
        # Step 1: Normalize filename
        normalized = normalize_filename(file_path.name)

        # Step 2: Convert double letters to single lowercase
        converted = convert_double_letter(normalized)

        # Step 3: Parse to get components
        try:
            subject_id, eye, remainder = parse_filename(converted)
        except ValueError as e:
            print(f"Skipping {file_path.name}: {e}")
            continue

        # Step 4: Build destination path
        dest_dir = source_dir / f"Control_{subject_id}" / eye
        short_name = f"C{subject_id}_{remainder}.tiff"
        dest_path = dest_dir / short_name

        # Display the operation
        print(f"{file_path.name} -> {dest_path.relative_to(source_dir)}")

        # Step 5: Create directory and move file
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            file_path.rename(dest_path)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reorganize Control image files into directory structure"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing the .tif files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files"
    )

    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Error: {args.directory} is not a valid directory")
        return

    process_files(args.directory, dry_run=args.dry_run)

    if not args.dry_run:
        print("\nDone!")


if __name__ == "__main__":
    main()

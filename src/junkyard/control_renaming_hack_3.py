#!/usr/bin/env python3

import argparse
from pathlib import Path


def rename_tiff_files(root_dir: Path, dry_run: bool = False) -> None:
    """Find and rename TIFF files in OD/OS subdirectories."""

    for eye_dir in root_dir.rglob('*'):
        if eye_dir.is_dir() and eye_dir.name in ('OD', 'OS'):
            eye = eye_dir.name

            for tiff_file in eye_dir.glob('*.tiff'):
                # Skip if eye already in filename
                if eye in tiff_file.stem:
                    continue

                # Split filename and insert eye at second position
                parts = tiff_file.stem.split('_')
                if len(parts) >= 2:
                    parts.insert(1, eye)
                    new_name = '_'.join(parts) + tiff_file.suffix
                    new_path = tiff_file.parent / new_name

                    if dry_run:
                        print(f"Would rename: {tiff_file} -> {new_path}")
                    else:
                        tiff_file.rename(new_path)
                        print(f"Renamed: {tiff_file} -> {new_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename TIFF files in OD/OS subdirectories"
    )
    parser.add_argument('directory', type=Path, help='Root directory to search')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would be renamed without actually renaming'
    )

    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Error: {args.directory} is not a valid directory")
        return

    rename_tiff_files(args.directory, args.dry_run)


if __name__ == '__main__':
    main()
#! /usr/bin/env python3

import os
import sys
import re
from pathlib import Path
from typing import Optional, Tuple


def parse_path(filepath: Path) -> Optional[Tuple[str, str, str, str]]:
    """Parse the filepath to extract patient, eye, and version info."""
    parts = filepath.parts
    if len(parts) < 3:
        return None

    # Check pattern: Control_<letter>/<eye>/something_<int1>_<int2>.tiff
    parent_dir = parts[-3]
    eye_dir = parts[-2]
    filename = parts[-1]

    # Match Control_<letter>
    control_match = re.match(r'^Control_([A-Za-z])$', parent_dir)
    if not control_match:
        return None

    letter = control_match.group(1)

    # Match filename pattern: *_<int1>_<int2>.tiff
    file_match = re.match(r'^.+_(\d+)_(\d+)\.tiff$', filename)
    if not file_match:
        return None

    int1, int2 = file_match.groups()

    return (letter, eye_dir, int1, int2)


def find_tiff_files(root_dir: str, output_file: str) -> None:
    """Find all matching TIFF files and write to TSV."""
    root_path = Path(root_dir).resolve()

    with open(output_file, 'w') as f:
        # Write header
        f.write("patient alias\timage path\teye\tage acquired\tdevice\tdilated\n")

        # Walk through directory tree
        for tiff_file in root_path.rglob("*.tiff"):
            result = parse_path(tiff_file)
            if result:
                letter, eye, int1, int2 = result
                patient_alias = f"Control {letter}"
                age = f"{int1}.{int2}"

                f.write(f"{patient_alias}\t{tiff_file}\t{eye}\t{age}\tSilverstone\t1\n")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <top_level_directory> <output_tsv>")
        sys.exit(1)

    root_dir = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.isdir(root_dir):
        print(f"Error: {root_dir} is not a valid directory")
        sys.exit(1)

    find_tiff_files(root_dir, output_file)
    print(f"TSV file created: {output_file}")


if __name__ == "__main__":
    main()

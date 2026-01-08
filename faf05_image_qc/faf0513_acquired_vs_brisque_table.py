#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import numpy as np
from matplotlib.lines import Line2D

from utils.db_utils import db_connect

#!/usr/bin/env python3
"""Plot brisque_score vs pixel_score with colors based on image path."""

from typing import Tuple
import matplotlib.pyplot as plt

from models.abca4_results import Score
from models.abca4_faf_models import FafImage


def fetch_scores() -> list[Tuple[float, float, str]]:
    """Fetch brisque_score, pixel_score, and image_path from database."""
    query = (
        Score
        .select(Score.brisque_score, FafImage.age_acquired,  FafImage.image_path)
        .join(FafImage)
        .tuples()
    )
    return list(query)


def get_case_info(image_path: str) -> list:
    """Return color based on whether image_path contains 'control'."""

    faf_img = FafImage.get(FafImage.image_path == image_path)
    alias = faf_img.case_id.alias
    eye = faf_img.eye
    device = faf_img.device.name
    dilated = faf_img.dilated
    is_control = faf_img.case_id.is_control

    return [alias, eye,  device, dilated, is_control]

def scores2table(data: list[tuple[float, float, str]]) -> None:
    """Create and display scatter plot of brisque vs age image acquired."""

    outf = open("brisque_scores.tsv", "w")
    print("\t".join(['alias', 'is_control', 'age', 'eye', 'dilated', 'device', 'brisque' ]), file=outf)
    for brisque, age, image_path in data:
        # print(brisque, pixel, path)
        if brisque is  None or age is  None: continue
        [alias, eye, device, dilated, is_control] = get_case_info(image_path)
        print("\t".join(str(s) for s in [alias, is_control, age, eye, dilated, device, brisque ]), file=outf)
    outf.close()

def main() -> None:
    """Fetch data and create scatter plot."""
    db = db_connect()
    data = fetch_scores()
    scores2table(data)
    db.close()

if __name__ == "__main__":
    main()
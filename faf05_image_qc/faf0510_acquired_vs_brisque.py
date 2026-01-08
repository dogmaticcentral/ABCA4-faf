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


def get_marker_style(image_path: str) -> tuple[str, str]:
    """Return color based on whether image_path contains 'control'."""

    faf_img = FafImage.get(FafImage.image_path == image_path)
    device = faf_img.device.name
    if device == "Silverstone":
        color = "orange"
    elif device == "California":
        color =  "red"
    else:
        color =  "pink"

    dilated = faf_img.dilated
    shape = 'o' if dilated else 'd' # o is circle d is thin diamond

    return color, shape

def get_legend_elements():
    return [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
               markersize=10, label='California'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange',
               markersize=10, label='Silverstone'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='pink',
               markersize=10, label='Daytona'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markersize=10, label='dilated'),
        Line2D([0], [0], marker='d', color='w', markerfacecolor='gray',
               markersize=8, label='not dilated'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='white',
               markeredgecolor='blue', markeredgewidth=2, markersize=10,
               label='patient'),
    ]

def plot_scores(data: list[tuple[float, float, str]]) -> None:
    """Create and display scatter plot of brisque vs age image acquired."""

    plt.figure(figsize=(10, 6))
    for brisque, age, image_path in data:
        # print(brisque, pixel, path)
        if brisque is  None or age is  None: continue
        color, shape = get_marker_style(image_path)
        # mec = 'markeredgecolor'
        if "control" in image_path.lower():
            mec = color
        else:
            mec = 'blue'
        # s = marker size
        plt.scatter(age, brisque, facecolors=color, edgecolors=mec, linewidths=3, marker=shape,  alpha=0.6, s=80)
    plt.legend(handles=get_legend_elements(), loc='lower right', fontsize=12)
    plt.xlabel("Age image acquired (years)", fontsize=14)
    plt.ylabel("BRISQUE Score", fontsize=14)
    # plt.title("BRISQUE Score vs Age image acquired")
    plt.grid(True, alpha=0.3)
    plt.show()


def main() -> None:
    """Fetch data and create scatter plot."""
    db = db_connect()
    data = fetch_scores()
    plot_scores(data)
    db.close()

if __name__ == "__main__":
    main()
#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import numpy as np

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


def get_marker_color(image_path: str) -> str:
    """Return color based on whether image_path contains 'control'."""
    if "control" in image_path.lower():
        device = FafImage.get(FafImage.image_path == image_path).device.name
        if device == "Silverstone":
            return "orange"
        elif device == "California":
            return "red"
        else:
            return "pink"
    else:
        return "blue"


def get_marker_shape(image_path: str) -> str:
    """Return color based on whether image_path contains 'control'."""

    width = FafImage.get(FafImage.image_path == image_path).width
    if width == 4000:
        return "s"

    return "o"



def plot_scores(data: list[tuple[float, float, str]]) -> None:
    """Create and display scatter plot of brisque vs age image acquired."""
    brisque_scores = []
    age_acquired = []
    colors = []
    shapes = []
    for brisque, age, path in data:
        # print(brisque, pixel, path)
        if brisque is not None and age is not None:
            brisque_scores.append(brisque)
            age_acquired.append(age)
            colors.append(get_marker_color(path))
            shapes.append(get_marker_shape(path))
    age_acquired   = np.array(age_acquired)
    brisque_scores = np.array(brisque_scores)
    colors =  np.array(colors)
    markers =  np.array(shapes)
    # Split by marker type
    mask = {'o':  markers == 'o', 's': markers == 's'}
    plt.figure(figsize=(10, 6))
    for shape in shapes:
        plt.scatter(age_acquired[mask[shape]], brisque_scores[mask[shape]], c=colors[mask[shape]], marker=shape, alpha=0.6, s=50)
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
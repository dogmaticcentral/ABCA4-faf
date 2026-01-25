#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.db_utils import db_connect
from faf00_settings import global_db_proxy

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
        .select(Score.brisque_score, Score.pixel_score_auto, FafImage.image_path)
        .join(FafImage)
        .tuples()
    )
    return list(query)


def get_marker_color(image_path: str) -> str:
    """Return color based on whether image_path contains 'control'."""
    return "red" if "control" in image_path.lower() else "blue"


def plot_scores(data: list[tuple[float, float, str]]) -> None:
    """Create and display scatter plot of brisque vs pixel scores."""
    brisque_scores = []
    pixel_scores = []
    colors = []

    for brisque, pixel, path in data:
        # print(brisque, pixel, path)
        if brisque is not None and pixel is not None:
            brisque_scores.append(brisque)
            pixel_scores.append(pixel)
            colors.append(get_marker_color(path))

    plt.figure(figsize=(10, 6))
    plt.scatter(pixel_scores, brisque_scores, c=colors, alpha=0.6, s=50)
    plt.xlabel("Pixel Score")
    plt.ylabel("BRISQUE Score")
    plt.title("BRISQUE Score vs Pixel Score")
    plt.grid(True, alpha=0.3)
    plt.show()


def main() -> None:
    """Fetch data and create scatter plot."""
    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)
    data = fetch_scores()
    plot_scores(data)
    
    if not db.is_closed():
        db.close()

if __name__ == "__main__":
    main()
#! /usr/bin/env python3
"""
Compare histograms of column 5 from two TSV files with special highlighting.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from typing import Tuple
import numpy as np


def load_file(filepath: str) -> Tuple[list[float], list[int], list[int]]:
    """Load columns 2, 3, and 5 from TSV file."""
    df = pd.read_csv(filepath, sep='\t')
    col2 = df.iloc[:, 1].astype(int).tolist()
    col3 = df.iloc[:, 2].astype(int).tolist()
    col5 = df.iloc[:, 4].astype(float).tolist()
    return col5, col2, col3


def calculate_plot_params(data_a: list[float], data_b: list[float]) -> Tuple[float, float, float]:
    """Calculate bin width and plot range based on combined data."""
    combined = data_a + data_b
    min_val = min(combined)
    max_val = max(combined)
    data_range = max_val - min_val
    bin_width = data_range / 30
    return min_val, max_val, bin_width


def find_highlighted_bins(col5: list[float], col2: list[int], col3: list[int],
                          bins: list[float]) -> set[int]:
    """Find bin indices where col3 (height) equals 4000."""
    highlighted = set()
    for val, w, h in zip(col5, col2, col3):
        if h != 4000 or w != 4000: continue
        bin_idx = np.searchsorted(bins, val) - 1
        if 0 <= bin_idx < len(bins) - 1:
            highlighted.add(bin_idx)

    return highlighted


def plot_histograms(data_a: list[float], data_b: list[float], col2_a: list[int],
                    col3_a: list[int], col2_b: list[int], col3_b: list[int],
                    min_val: float, max_val: float, bin_width: float) -> None:
    """Plot normalized histograms with orange borders on highlighted bins."""
    data_range = max_val - min_val
    bins = [min_val + i * bin_width for i in range(int(data_range / bin_width) + 2)]

    highlighted_a = find_highlighted_bins(data_a, col2_a, col3_a, bins)
    highlighted_b = find_highlighted_bins(data_b, col2_b, col3_b, bins)

    fig, ax = plt.subplots(figsize=(10, 6))

    counts_b, _, patches_b = ax.hist(data_b, bins=bins, density=True, alpha=0.8,
                                     color='red', label='Controls')
    counts_a, _, patches_a = ax.hist(data_a, bins=bins, density=True, alpha=0.8,
                                     color='blue', label='Patients')

    for idx in highlighted_a:
        if idx < len(patches_a):
            patches_a[idx].set_edgecolor('orange')
            patches_a[idx].set_linewidth(8)

    for idx in highlighted_b:
        if idx < len(patches_b):
            patches_b[idx].set_edgecolor('orange')
            patches_b[idx].set_linewidth(8)

    ax.set_xlabel('BRISQUE score', fontsize=14)
    ax.set_ylabel('Normalized Frequency', fontsize=14)
    # ax.set_title('Histogram Comparison for the BRISQUE score')
    legend_elements = [Patch(facecolor='blue', alpha=0.6, label='Patients'),
                       Patch(facecolor='red', alpha=0.6, label='Controls'),
                       Patch(facecolor='white', edgecolor='orange', linewidth=3, label='4000')]
    ax.legend(handles=legend_elements, fontsize=12)


    plt.tight_layout()
    plt.show()


def main() -> None:
    """Main function."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file_a.tsv> <file_b.tsv>")
        sys.exit(1)

    file_a = sys.argv[1]
    file_b = sys.argv[2]

    data_a, col2_a, col3_a = load_file(file_a)
    data_b, col2_b, col3_b = load_file(file_b)

    min_val, max_val, bin_width = calculate_plot_params(data_a, data_b)
    plot_histograms(data_a, data_b, col2_a, col3_a, col2_b, col3_b,
                    min_val, max_val, bin_width)


if __name__ == '__main__':
    main()
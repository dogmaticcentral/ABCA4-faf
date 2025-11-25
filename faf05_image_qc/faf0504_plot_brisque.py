#!/usr/bin/env python3
"""
Compare histograms of column 5 from two TSV files.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple


def load_file_a(filepath: str) -> list[float]:
    """Load column 5 from file A, skipping rows where column 2 equals 4000."""
    df = pd.read_csv(filepath, sep='\t')
    df = df[df.iloc[:, 1] != 4000]
    return df.iloc[:, 4].astype(float).tolist()


def load_file_b(filepath: str) -> list[float]:
    """Load column 5 from file B as floats."""
    df = pd.read_csv(filepath, sep='\t')
    return df.iloc[:, 4].astype(float).tolist()


def calculate_plot_params(data_a: list[float], data_b: list[float]) -> Tuple[float, float, float]:
    """Calculate bin width and plot range based on combined data."""
    combined = data_a + data_b
    min_val = min(combined)
    max_val = max(combined)
    data_range = max_val - min_val
    bin_width = data_range / 30
    return min_val, max_val, bin_width


def plot_histograms(data_a: list[float], data_b: list[float], min_val: float,
                    max_val: float, bin_width: float) -> None:
    """Plot normalized histograms for both datasets."""
    data_range = max_val - min_val
    bins = [min_val + i * bin_width for i in range(int(data_range / bin_width) + 2)]

    plt.figure(figsize=(10, 6))
    plt.hist(data_a, bins=bins, density=True, alpha=0.6, color='blue', label='Patients')
    plt.hist(data_b, bins=bins, density=True, alpha=0.6, color='red', label='Controls')
    plt.xlabel('BRISQUE Score', fontsize=18)
    plt.ylabel('Normalized Frequency', fontsize=18)
    plt.title('BRISQUE Score Histogram Comparison', fontsize=26)
    plt.legend(fontsize=18)
    plt.tight_layout()
    plt.show()


def main() -> None:
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: script.py <file_a.tsv> <file_b.tsv>")
        sys.exit(1)

    file_a = sys.argv[1]
    file_b = sys.argv[2]

    data_a = load_file_a(file_a)
    data_b = load_file_b(file_b)

    min_val, max_val, bin_width = calculate_plot_params(data_a, data_b)
    plot_histograms(data_a, data_b, min_val, max_val, bin_width)


if __name__ == '__main__':
    main()

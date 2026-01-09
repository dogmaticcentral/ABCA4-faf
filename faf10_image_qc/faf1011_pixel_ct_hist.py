#!/usr/bin/env python3
"""
Script to plot two overlapping histograms from a TSV file.
One histogram for 'control' names, another for all other names.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Plot overlapping histograms from a two-column TSV file."
    )
    parser.add_argument(
        "filename",
        type=str,
        help="Path to the TSV file with 'name' and 'value' columns"
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=30,
        help="Number of histogram bins (default: 30)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for the plot (optional, displays if not provided)"
    )
    return parser.parse_args()


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load TSV file into a DataFrame.

    Args:
        filepath: Path to the TSV file.

    Returns:
        DataFrame with 'name' and 'value' columns.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is invalid.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(filepath, sep='\t', header=None, names=['name', 'value'])

    if df.shape[1] != 2:
        raise ValueError("TSV file must have exactly two columns")

    # Convert value column to numeric
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    # Remove rows with NaN values
    initial_rows = len(df)
    df = df.dropna(subset=['value'])
    dropped_rows = initial_rows - len(df)

    if dropped_rows > 0:
        print(f"Warning: Dropped {dropped_rows} rows with non-numeric values")

    return df


def split_by_control(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Split data into control and non-control groups.

    Args:
        df: DataFrame with 'name' and 'value' columns.

    Returns:
        Tuple of (control_values, other_values) Series.
    """
    # Case-insensitive check for 'control' in the name
    is_control = df['name'].str.lower().str.contains('control', na=False)

    control_values = df.loc[is_control, 'value']
    other_values = df.loc[~is_control, 'value']

    return control_values, other_values


def plot_histograms(
        control_values: pd.Series,
        other_values: pd.Series,
        output_path: str | None = None
) -> None:
    """
    Plot overlapping histograms for control and non-control groups.

    Args:
        control_values: Values for the control group.
        other_values: Values for the non-control group.
        bins: Number of histogram bins.
        output_path: Optional path to save the figure.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    binwidth = 20000
    # Calculate bin edges based on all data
    all_values = pd.concat([control_values, other_values])
    bin_min = int(all_values.min() // binwidth * binwidth)
    bin_max = int(all_values.max() // binwidth * binwidth + binwidth)
    bin_edges = range(bin_min, bin_max + binwidth, binwidth)

    # Plot histograms with transparency for overlap visibility
    ax.hist(
        control_values,
        bins=bin_edges,
        alpha=0.6,
        label=f'Control (n={len(control_values)})',
        color='steelblue',
        edgecolor='black',
        linewidth=0.5,
        weights=np.ones(len(control_values)) / len(control_values)
    )

    ax.hist(
        other_values,
        bins=bin_edges,
        alpha=0.6,
        label=f'Patients (n={len(other_values)})',
        color='coral',
        edgecolor='black',
        linewidth=0.5,
        weights=np.ones(len(other_values)) / len(other_values)
    )

    # Customize the plot
    ax.set_xlabel('Value', fontsize=16)
    ax.set_ylabel('Fraction', fontsize=16)
    ax.set_title('Distribution of the number of pixels per ellipse', fontsize=14)
    ax.legend(loc='upper right', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
    else:
        plt.show()


def main() -> int:
    """
    Main function to orchestrate the histogram plotting.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_arguments()

    try:
        # Load and process data
        df = load_data(args.filename)
        print(f"Loaded {len(df)} rows from {args.filename}")

        # Split into control and non-control groups
        control_values, other_values = split_by_control(df)
        # Check if we have data to plot
        if len(control_values) == 0 and len(other_values) == 0:
            print("Error: No valid data to plot")
            return 1

        if len(control_values) == 0:
            print("Warning: No 'control' samples found")

        if len(other_values) == 0:
            print("Warning: No non-control samples found")

        print(f"Control group: {len(control_values)} samples")
        print(f"  Mean: {control_values.mean():.0f}")
        print(f"  Std Dev: {control_values.std():.0f}")
        print(f"Patient group: {len(other_values)} samples")
        print(f"  Mean: {other_values.mean():.0f}")
        print(f"  Std Dev: {other_values.std():.0f}")
        t_stat, p_value = stats.ttest_ind(control_values, other_values)
        print(f"Two-sample t-test:")
        print(f"  t-statistic: {t_stat:.4f}")
        print(f"  p-value: {p_value:.4e}")
        
        # Create the plot
        plot_histograms(
            control_values,
            other_values,
            output_path=args.output
        )

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

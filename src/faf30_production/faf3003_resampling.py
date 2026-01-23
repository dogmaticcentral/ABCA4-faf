#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import correlation
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from statistics import mean

from sys import argv

import scipy.stats as stats
from random import sample

from utils.db_utils import db_connect
from faf30_production.faf3001_score_vs_time_plot import individual_eye_scores, average_eye_scores


def improvized_arg_parser() -> tuple:
    if len(argv) > 1 and argv[1] in ["-h", "--help"]:
        print(f"{argv[0]} [-h/--help] | [-a/--avg] [-l/--latex]")
        exit()
    average = len({"-a", "--avg"}.intersection(argv)) > 0
    latex = len({"-l", "--latex"}.intersection(argv)) > 0

    return average, latex


def subsample(df_cases, subsample_size, verbose=False) -> list[float]:
    n_points = len(df_cases["age"])
    n_iters = 508
    lower_cis = []
    upper_cis = []
    spearman_corrs = []

    for i in range(1, n_iters + 1):
        sampling_index = sample(range(n_points), subsample_size)
        x = [df_cases["age"][i] for i in sampling_index]
        y = [df_cases["pixel_score"][i] for i in sampling_index]

        corr_coefficient, p_value = stats.spearmanr(x, y)
        if verbose:
            # Calculate confidence intervals for Spearman correlation
            alpha = 0.05  # significance level for 95% CI
            # Using the 'correlation' library to calculate confidence intervals
            lower_ci, upper_ci = correlation.corr(x, y, method='spearman_rho', alpha=alpha)[1:3]
            print(f"subsample {i}")
            print(f"Spearman Correlation Coefficient: {corr_coefficient:.4f}")
            print(f"P-value: {p_value:.4f}")
            print(f"95% Confidence Interval: ({lower_ci:.4f}, {upper_ci:.4f})")
            print()
            lower_cis.append(lower_ci)
            upper_cis.append(upper_ci)
        spearman_corrs.append(corr_coefficient)

    if verbose:
        mean_corr  = mean(spearman_corrs)
        mean_lower = mean(lower_cis)
        mean_upper = mean(upper_cis)
        print(f"{subsample_size:3d}  {mean_corr:.3f}   {mean_lower:.3f}  {mean_upper:.3f}")

    return spearman_corrs


def plot_whiskas(spearman_corr_distros):
    """ Whisker plot for distributions of corrs"""
    bigfont = 26
    smallfont = 20
    ticklabelfont = 14
    # Multiple box plots on one axis
    fig, ax = plt.subplots()
    # fig.suptitle("S", fontsize=bigfont)
    # 0, '' mean: "don't show outlier points"
    ax.boxplot(spearman_corr_distros, 0, '')
    n = len(spearman_corr_distros)
    original_ticks = list(range(1, n + 1))
    new_ticks = [str(10 + (i-1)*5) for i in original_ticks]

    ax.tick_params(labelsize=ticklabelfont)
    ax.set_xticks(original_ticks, new_ticks)
    ax.set_xlabel('Subsample size', fontsize=smallfont)
    ax.set_ylabel('Spearman correlation', fontsize=smallfont)
    plt.tight_layout()
    plt.show()
    # fnm = "subsampling.png"
    # plt.savefig(fnm)
    # print(f"wrote {fnm}")


def main():

    (average, latex) = improvized_arg_parser()

    db = db_connect()  # this initializes global proxy
    if average:
        ret_dict = average_eye_scores()
        df_cases = pd.DataFrame.from_dict(ret_dict)
    else:
        ret_dict = individual_eye_scores()
        df_cases = pd.DataFrame.from_dict(ret_dict)
    db.close()

    spearman_corr_distros = [subsample(df_cases, subsample_size) for subsample_size in range(10, len(df_cases), 5)]
    plot_whiskas(spearman_corr_distros)


########################
if __name__ == "__main__":
    main()

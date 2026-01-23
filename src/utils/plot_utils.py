#! /usr/bin/env python
from random import random, randint

import scipy

_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

# if matplotlib is not instructed to use Agg it tries to use Xorg for a GUI (that we do not need here)
# and then screams booldy murder about "main thread is not in main loop" if we try to use it ina multithreaded context
# https://stackoverflow.com/questions/4931376/generating-matplotlib-graphs-without-a-running-x-server#4935945
# https://en.wikipedia.org/wiki/X.Org_Server
# this has something to do with Tkinter not being fully thread safe is practice, but I did not investigate further
# https://stackoverflow.com/questions/14694408/runtimeerror-main-thread-is-not-in-main-loop#14695007

import matplotlib
from sklearn.mixture import GaussianMixture

from utils.utils import is_nonempty_file
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as grid_spec


def plot_histogram(histogram: list, fig_path, title,
                   fitted_gaussians: GaussianMixture | None = None, weights=None,
                   color="blue", skip_if_exists: bool = False):

    matplotlib.use('Agg')
    if skip_if_exists and is_nonempty_file(fig_path):
        print(f"{fig_path} found")
        return fig_path

    fig, axs = plt.subplots(1)
    fig.suptitle(title if title else f'histogram ')
    axs.set(xlabel='intensity', ylabel='fraction of pixels')
    norm = sum(histogram)
    probs = [count/norm for count in histogram]
    x_points = list(range(len(histogram)))
    x = np.array(x_points).reshape(-1, 1)

    if fitted_gaussians is not None and weights is not None:
        logprob = fitted_gaussians.score_samples(x.reshape(-1, 1))
        pdf = np.exp(logprob)
        pdf_gaussian_components = weights * pdf[:, np.newaxis]

        axs.plot(x_points, pdf, '-', color='orange', label='fitted Gaussian')
        axs.plot(x_points, pdf_gaussian_components, '--', color='orange')
        axs.plot(x_points, probs, color=color, label="histogram points")
        axs.legend(loc='upper right')

    else:
        axs.plot(x_points, probs, color=color)
    plt.savefig(fig_path)
    plt.close()


# https://blog.scientific-python.org/matplotlib/create-ridgeplots-in-matplotlib/
def plot_graph_series(Y, labels, colors, x_label=None, plot_title=None, fig_path=None):
    """
    :param Y:  list of lists of values at points given by the list index - a graph series
    :param labels: list of labels (strings), for each list in Y
    :param colors: colors for each list of values - will be recycled if len(colors) too short
    :param x_label: label for the x-axis
    :return:
    """

    gs = grid_spec.GridSpec(len(labels), 1)
    fig = plt.figure()
    if plot_title: fig.suptitle(plot_title, fontsize=20)
    ax_objs = []
    x_min = 0
    x_max = max(len(y) for y in Y)
    y_min = min(min(y) for y in Y)
    y_max = max(max(y) for y in Y)
    for i, label in enumerate(labels):
        y = Y[i]
        x = list(range(len(y)))
        # creating new axes object
        ax_objs.append(fig.add_subplot(gs[i:i+1, 0:]))

        # plotting the distribution
        ax_objs[-1].plot(x, y, color="#f0f0f0", lw=1)
        ax_objs[-1].fill_between(x, y, alpha=1, color=colors[i % len(colors)])

        # setting uniform x and y lims
        ax_objs[-1].set_xlim(x_min, x_max)
        ax_objs[-1].set_ylim(y_min, y_max)

        # make background transparent
        rect = ax_objs[-1].patch
        rect.set_alpha(0)

        # remove borders, axis ticks, and labels
        ax_objs[-1].set_yticklabels([])
        ax_objs[-1].set_yticks([])
        if i == len(labels)-1:
            if x_label:
                ax_objs[-1].set_xlabel(x_label, fontsize=18, labelpad=10)
        else:
            ax_objs[-1].set_xticklabels([])

        # the "spines" are the lines framing the figure
        spines = ["top", "right", "left", "bottom"]
        for s in spines:
            ax_objs[-1].spines[s].set_visible(False)

        ax_objs[-1].text(-0.1, 0, label, fontsize=16, ha="right")
    plt.xticks(fontsize=16)
    gs.update(hspace=-0.7)
    if fig_path:
        plt.savefig(fig_path)
    else:
        plt.show()
    plt.close()


###########################################
if __name__ == "__main__":
    # Create the data
    rs = np.random.RandomState(1979)
    timepoints = list("ABCDEF")
    X = []
    for _ in timepoints:
        distro = scipy.stats.norm(loc=100 + 20*(random()*2-1), scale=randint(10, 20))
        X.append([distro.pdf(i) for i in range(255)])
    nice_colors = ['#0000ff', '#3300cc', '#660099', '#990066', '#cc0033', '#ff0000']
    plot_graph_series(X, timepoints, nice_colors,  "this is the x-axis label", )


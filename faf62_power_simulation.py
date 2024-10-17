#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import matplotlib.pyplot as plt

import numpy as np
from itertools import chain
from scipy import stats

"""
https://modernstatisticswithr.com/modchapter.html
The power of a test is estimated as the proportion of simulations in which the null hypothesis was rejected. 

see also
https://www.colorado.edu/ibg/sites/default/files/attached-files/boulder_power_2022.pdf
"""

import math
from random import uniform, sample, normalvariate


def simulation(num_sims, sample_size, exp_factor, sigma, correlation, alpha) -> float:
    # rejection refers to rejecting the null hypothesis (= there is no correlation)
    rejected = 0
    for _ in range(num_sims):
        x = [uniform(0,10) for _ in range(sample_size)]
        y = [normalvariate(mu=math.exp(i*exp_factor), sigma=sigma) for i in x]
        spearman = stats.spearmanr(x, y)
        if spearman.statistic > correlation and spearman.pvalue < alpha:
            rejected += 1
    return rejected/num_sims


def plot(size, power):

    smallfont = 20
    ticklabelfont = 16

    fig, ax1 = plt.subplots(1, 1)
    ax1.tick_params(axis="x", which="major", labelsize=ticklabelfont)
    ax1.set_xlabel("Number of data points", fontsize=smallfont, labelpad=10)
    ax1.set_ylabel("Simulated power", fontsize=smallfont, labelpad=10)
    for i in range(2):
        ax1.plot(size, power[i], label=f"run {i+1}")
        ax1.scatter(size, power[i])

    ax1.legend(loc="lower right", prop={'size': 12})

    fig.tight_layout()
    plt.savefig("power.png")


def main():

    num_sims   = 1000
    exp_factor = 1.0
    sigma = 100.0
    correlation = 0.80
    alpha = 1.e-6

    size = []
    power = [[], []]
    for sample_size in chain (range(10, 39, 2),   range(40, 100, 5)):
        power0 = simulation(num_sims, sample_size, exp_factor, sigma, correlation, alpha)
        power1 = simulation(num_sims, sample_size, exp_factor, sigma, correlation, alpha)
        size.append(sample_size)
        power[0].append(power0)
        power[1].append(power1)
        print(f"N={sample_size}   power0={power0:.3f}  power1={power1:.3f}")

    plot(size, power)


########################
if __name__ == "__main__":
    main()


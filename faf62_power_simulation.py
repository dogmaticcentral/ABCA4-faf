#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
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


# TODO estimate the params od the exponential fit to the data
def simulation0(num_sims, sample_size, exp_factor, sigma,  effect_size, alpha) -> float:
    rejected = 0
    for _ in range(num_sims):
        x = [uniform(0,10) for _ in range(sample_size)]
        y = [normalvariate(mu=math.exp(i*exp_factor),sigma=sigma) for i in x]
        spearman = stats.spearmanr(x, y)
        if spearman.statistic > effect_size and spearman.pvalue < alpha:
            rejected += 1
    return rejected/num_sims

# TODO estimate the params od the exponential fit to the data
def simulation1(num_sims, sample_size, exp_factor, sigma, effect_size, alpha) -> float:
    correlation = effect_size
    rejected = 0
    for _ in range(num_sims):
        x = np.random.uniform(0, 10, sample_size)
        # Exponential behavior with noise
        y = np.random.exponential(scale=exp_factor, size=sample_size) + np.random.normal(scale=sigma, size=sample_size)
        # Apply a transformation to achieve the desired correlation
        y = stats.rankdata(y + correlation * (x - np.mean(x))) + np.random.normal(scale=sigma, size=sample_size)
        spearman = stats.spearmanr(x, y)
        if spearman.statistic > effect_size and spearman.pvalue < alpha:
            rejected += 1
    return rejected/num_sims


def main():

    num_sims   = 100
    exp_factor = 1.0
    sigma = 100.0
    effect_size = 0.80
    alpha = 1.e-3

    for sample_size in chain (range(5,30, 2),   range(30, 100, 5)):
        power0 = simulation0(num_sims, sample_size, exp_factor, sigma, effect_size, alpha)
        power1 = simulation0(num_sims, sample_size, exp_factor, sigma, effect_size, alpha)
        print(f"N={sample_size}   power0={power0:.3f}  power1={power1:.3f}")


########################
if __name__ == "__main__":
    main()


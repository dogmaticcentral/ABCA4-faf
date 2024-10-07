#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import numpy as np
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
def simulation0(num_sims, sample_size, sigma,  effect_size, alpha) -> float:
    rejected = 0
    for _ in range(num_sims):
        x = [uniform(0,10) for _ in range(sample_size)]
        y = [normalvariate(mu=math.exp(i*0.3),sigma=sigma) for i in x]
        spearman = stats.spearmanr(x, y)
        if spearman.statistic > effect_size and spearman.pvalue < alpha:
            rejected += 1
    return rejected/num_sims

# TODO estimate the params od the exponential fit to the data
def simulation1(num_sims, sample_size, sigma, effect_size, alpha) -> float:
    correlation = effect_size
    rejected = 0
    for _ in range(num_sims):
        x = np.random.uniform(0, 10, sample_size)
        y = np.random.exponential(scale=0.3, size=sample_size) + np.random.normal(scale=sigma, size=sample_size)  # Exponential behavior with noise
        # Apply a transformation to achieve the desired correlation
        y = stats.rankdata(y + correlation * (x - np.mean(x))) + np.random.normal(scale=sigma, size=sample_size)
        spearman = stats.spearmanr(x, y)
        if spearman.statistic > effect_size and spearman.pvalue < alpha:
            rejected += 1
    return rejected/num_sims



def main():

    num_sims = 100
    sigma = 2.0
    effect_size = 0.85
    alpha = 1.e-3

    for sample_size in range(10, 100, 5):
        power0 = simulation0(num_sims, sample_size, sigma, effect_size, alpha)
        power1 = simulation0(num_sims, sample_size, sigma, effect_size, alpha)
        print(f"N={sample_size}   power0={power0:.3f}  power1={power1:.3f}")

########################
if __name__ == "__main__":
    main()


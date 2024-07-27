_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

import math
import os.path
from multiprocessing import Process

import numpy as np
from matplotlib import pyplot as plt
from sklearn.mixture import GaussianMixture


def gaussian_mixture(histogram, n_comps_to_try: list[int] | None = None) -> tuple[GaussianMixture, list[float]]:

    unpacked_points = []
    for idx, count in enumerate(histogram): unpacked_points.extend([idx]*count)
    if len(unpacked_points) < 100:
        raise Exception("Too few points to fit Gaussian mixture")

    numpy_points = np.array(unpacked_points).reshape(-1,1)
    if not n_comps_to_try: n_comps_to_try = list(range(1, 6))
    models = [GaussianMixture(n_components, max_iter=10000, random_state=314).fit(numpy_points) for n_components in n_comps_to_try]

    min_akaike = 1.e10
    best_akaike_model: GaussianMixture = models[0]
    min_dist = 0.1
    akaike0 = None
    rel_akaike = None
    for idx, model in enumerate(models):
        # print(f"================= {idx + 1} ================")
        akaike = model.aic(numpy_points)
        if akaike < min_akaike:
            min_akaike = akaike
            best_akaike_model = model
        if akaike0 is None: akaike0 = akaike
        rel_akaike = (akaike - akaike0)/akaike0*1000
        #     print(f"Akaike information criterion {akaike:.2f}")
        #     print(f"Bayesian information criterion {model.bic(numpy_points):.2f}")
        #     # print(model.predict_proba(numpy_points))
        #     print(f"score {model.score(numpy_points):.2f}")
        #     # print(f"labels estimate {model.fit_predict(numpy_hist)}")
        stdevs = np.sqrt(model.covariances_)
        # print("-----------------------------------")
        # print(f"rel_akaike: {rel_akaike: .2e}   bg_mean {bg_mean: .0f}   bg_std {bg_std: .0f}")
        header = f"label    mean    stdev     weight"

        # print(header)
        for label in range(n_comps_to_try[idx]):
            mean = model.means_[label,0]
            std  = stdevs[label, 0, 0]
            out  = f"{label}     {mean:6.0f}   {std:6.0f}    {model.weights_[label]:5.2f} "
            # print(out)
    best_model = best_akaike_model
    # print(f"choosing the best model by Akaike criterion distance, {best_model.n_components} gaussians")
    # print()
    # copied from https://www.astroml.org/book_figures/chapter4/fig_GMM_1D.html
    x_points = list(range(len(histogram)))
    x = np.array(x_points).reshape(-1,1)
    # 'responsibilities' is the list of fractions with which each individual gaussian
    # contributes to the probability of the bin i
    # eg if we have 4 gaussians, this will  be a list of quads
    responsibilities = best_model.predict_proba(x.reshape(-1, 1))
    return best_model, responsibilities

import numpy as np
from scipy import stats
# pearson correlation for data wiht errorbars
def bootstrap_correlation(x, y, y_err, n_bootstrap=1000):
    """Bootstrap correlation accounting for y errors"""
    correlations = []

    for _ in range(n_bootstrap):
        # Generate new y values by sampling from normal distributions
        y_boot = np.random.normal(y, y_err)
        corr, _ = stats.pearsonr(x, y_boot)
        correlations.append(corr)

    correlations = np.array(correlations)
    mean_corr = np.mean(correlations)
    std_corr = np.std(correlations)

    return mean_corr, std_corr, correlations
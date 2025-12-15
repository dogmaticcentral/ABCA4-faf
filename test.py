#! /usr/bin/env python
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import scikits.bootstrap as boot

# Sample data
x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
y = np.array([2.1, 1.9, 6.2, 7.8, 5.3, 11.9, 14.2, 15.8, 18.1, 17.0])
y_err = np.array([0.5, 0.1, 0.4, 0.7, 0.5, 2.6, 0.8, 0.5, 1.7, 0.6])

# Method 1: Standard Pearson correlation (ignoring errors)
corr_pearson, p_value = stats.pearsonr(x, y)
print(f"Pearson correlation: {corr_pearson:.4f}")
print(f"P-value: {p_value:.4e}\n")


# Method 2: Weighted correlation (using inverse variance as weights)
def weighted_correlation(x, y, weights):
    """Calculate weighted Pearson correlation"""
    w_mean_x = np.average(x, weights=weights)
    w_mean_y = np.average(y, weights=weights)

    cov_xy = np.average((x - w_mean_x) * (y - w_mean_y), weights=weights)
    var_x = np.average((x - w_mean_x) ** 2, weights=weights)
    var_y = np.average((y - w_mean_y) ** 2, weights=weights)

    weighted_corr = cov_xy / np.sqrt(var_x * var_y)
    return weighted_corr


weights = 1 / y_err ** 2  # Inverse variance weighting
corr_weighted = weighted_correlation(x, y, weights)
print(f"Weighted correlation: {corr_weighted:.4f}\n")


# Method 3: Bootstrap to estimate correlation uncertainty
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


mean_corr, std_corr, boot_corrs = bootstrap_correlation(x, y, y_err, n_bootstrap=10000)
print(f"Bootstrap correlation: {mean_corr:.4f} ± {std_corr:.4f}")
print(f"95% CI: [{np.percentile(boot_corrs, 2.5):.4f}, {np.percentile(boot_corrs, 97.5):.4f}]")


# Method 4: Spearman rank correlation (robust to outliers)
corr_spearman, p_value_spearman = stats.spearmanr(x, y)
print(f"Spearman correlation: {corr_spearman:.4f}")
print(f"P-value: {p_value_spearman:.4e}\n")

# Visualization
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Data with error bars
axes[0].errorbar(x, y, yerr=y_err, fmt='o', capsize=5, label='Data with errors')
axes[0].set_xlabel('x')
axes[0].set_ylabel('y')
axes[0].set_title(f'Data (r = {corr_pearson:.3f})')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Plot 2: Bootstrap distribution
axes[1].hist(boot_corrs, bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(mean_corr, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_corr:.3f}')
axes[1].axvline(np.percentile(boot_corrs, 2.5), color='orange', linestyle=':', label='95% CI')
axes[1].axvline(np.percentile(boot_corrs, 97.5), color='orange', linestyle=':')
axes[1].set_xlabel('Correlation coefficient')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Bootstrap Distribution of Correlation')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
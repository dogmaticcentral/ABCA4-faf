import dask
from statistics import mean

import numpy as np
from scipy.spatial import cKDTree

from numpy.typing import ArrayLike, NDArray


def zscore_normalize(x: ArrayLike) -> NDArray[np.float32]:
    x = np.asarray(x)
    return (x - x.mean()) / x.std()


def mean_point_density(x, y):
    """
    Compute the mean spatial density of 2D points using a Gaussian kernel and KD-Tree for efficient neighbor searches.

    For each point, the density is estimated by summing exponentially weighted distances
    to its neighbors within a fixed radius. The weights decay with distance (Gaussian kernel),
    giving higher influence to closer points. The mean of all point densities is returned.

    Parameters
    ----------
    x : array_like
        1D array of x-coordinates of the points.
    y : array_like
        1D array of y-coordinates of the points (must match length of `x`).

    Returns
    -------
    float
        Mean density of all points. Higher values indicate tighter clustering.

    Notes
    -----
    - Uses a fixed search radius (`radius=10.0`) and Gaussian kernel weights (`exp(-distances²)`).
    - A KD-Tree (`scipy.spatial.cKDTree`) accelerates neighbor searches from O(N²) to ~O(N log N).
    - Suitable for low-dimensional (2D/3D) data. For higher dimensions, consider alternative methods.

    Example
    -------
    >>> x = np.random.rand(100)  # Random x-coordinates
    >>> y = np.random.rand(100)  # Random y-coordinatesI
    >>> mean_density = mean_point_density(x, y)
    >>> print(f"Mean point density: {mean_density:.2f}")

    Args:
        scale_x:
    """
    # Organize data into a 2D array (n points x 2 dimensions)
    points = np.column_stack((x, y))

    # A KD-Tree (k-dimensional tree) is a space-partitioning data structure
    # designed for organizing points in a k-dimensional space (in this case, 2D)
    tree = cKDTree(points)
    densities = np.zeros(points.shape[0])
    radius = 10
    for i, point in enumerate(points):
        # Find neighbors within radius
        idx = tree.query_ball_point(point, r=radius)
        distances = np.linalg.norm(points[idx] - point, axis=1)

        weights = np.exp(-(distances/0.5)**2)

        # Sum weights as density estimate
        densities[i] = np.sum(weights)

    return mean(densities)


def two_scenario_mpd_comparison(x, x_alt, y) -> tuple[float, float]:
    scale_y  = np.std(y)
    y_scaled = (y - np.mean(y)) / scale_y

    global_x = np.concatenate([x, x_alt])  # all x from all datasets
    scale_x  = np.std(global_x)

    x_scaled = (x - np.mean(global_x)) / scale_x
    mpd = mean_point_density(x_scaled, y_scaled)

    x_alt_scaled = (x_alt - np.mean(global_x)) / scale_x
    mpd_alt = mean_point_density(x_alt_scaled, y_scaled)

    return mpd, mpd_alt


def simulation_task(x, y, x_alt_generator, generator_params: dict, ref_difference, seed=None) -> bool:
    """
    Perform a single simulation with an independent RNG instance.

    Args:
        x, y: Input data for comparison
        x_alt_generator: Callback function to generate alternative scenario
        generator_params: Parameters for the generator
        ref_difference: Reference difference to compare against
        seed: Seed value to initialize an independent RNG stream

    Returns:
        bool: Whether the simulated difference exceeds the reference
    """
    # Create an independent RNG instance for this task
    rng = None if seed is None else np.random.default_rng(seed)
    modified_generator_params = generator_params.copy()
    modified_generator_params['rng'] = rng
    x_alt_simulated = x_alt_generator(**modified_generator_params)
    mean_density, mean_density_simulated = two_scenario_mpd_comparison(x, x_alt_simulated, y)
    diff = mean_density_simulated - mean_density
    return diff > ref_difference


from dask import delayed
from tqdm.auto import tqdm


def two_scenario_p_value_parallel(x, x_alt, y, x_alt_generator, generator_params: dict, n_simulations=1000,
                                 base_seed=42,  verbose=False):
    """
    Calculate p-value using parallel simulations with independent RNG streams.

    Args:
        x, x_alt, y: Input data for comparison
        x_alt_generator: Callback function to generate alternative scenario
        generator_params: Parameters for the generator
        n_simulations: Number of simulations to run
        verbose: Whether to print progress and debug information
        base_seed: Base seed for reproducible independent RNG streams

    Returns:
        float: P-value as the proportion of simulations exceeding reference difference
    """
    # Calculate reference difference once
    mean_density, mean_density_alt = two_scenario_mpd_comparison(x, x_alt, y)
    ref_difference = mean_density_alt - mean_density

    # Create independent seeds for each simulation using SeedSequence for reproducibility
    # This ensures statistically independent streams for each task
    seed_seq = np.random.SeedSequence(base_seed)
    child_seeds = seed_seq.spawn(n_simulations)  # Spawn independent seed sequences for each task

    # Create delayed tasks for parallel execution
    delayed_tasks = [
        delayed(simulation_task)(x, y, x_alt_generator, generator_params, ref_difference, seed=child_seeds[i])
        for i in range(n_simulations)
    ]

    # Compute results in parallel
    if verbose:
        with tqdm(total=n_simulations, desc="Simulations") as pbar:
            results = dask.compute(*delayed_tasks, scheduler='processes')
            pbar.update(n_simulations)
    else:
        results = dask.compute(*delayed_tasks, scheduler='processes')

    # Count occurrences where difference exceeds reference
    number_of_bigger_density_occurrences = sum(results)

    if verbose:
        print(f"Reference Difference: {ref_difference}, Bigger Density Occurrences: {number_of_bigger_density_occurrences}")

    return number_of_bigger_density_occurrences / n_simulations


def two_scenario_p_value(x, x_alt, y,  x_alt_generator, generator_params: dict, n_simulations=1000, verbose=False):

    mean_density, mean_density_alt = two_scenario_mpd_comparison(x, x_alt, y)
    ref_difference = mean_density_alt - mean_density
    results = [simulation_task(x, y, x_alt_generator, generator_params, ref_difference, None) for _ in range(n_simulations)]
    number_of_bigger_density_occurences  = sum(results)

    if verbose:
        print(ref_difference,  number_of_bigger_density_occurences)

    return number_of_bigger_density_occurences/n_simulations



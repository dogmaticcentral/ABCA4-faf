import numpy as np

from utils.ndarray_utils import extremize


def test_extremize():
    sample_array = np.array([[50, 150, 200], [80, 120, 90], [300, 40, 110]])
    print(f"Original Array of the type {type(sample_array)}:")
    print(sample_array)

    # Specify a threshold
    for cutoff in [100, 600]:

        # Apply the function with the specified threshold
        modified_array = extremize(sample_array, cutoff=cutoff)
        print("\nModified Array with threshold", cutoff, ":")
        print(modified_array)


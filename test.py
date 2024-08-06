import numpy as np


def set_elements_below_threshold(arr, threshold=100):
    """
    Set all elements of the input 2D array to 0 if they are smaller than the specified threshold.

    Parameters:
    arr (np.ndarray): Input two-dimensional NumPy array.
    threshold (int): The threshold value below which elements will be set to 0.

    Returns:
    np.ndarray: Modified array with elements below the threshold set to 0.
    """

    # Define a function to apply
    def threshold_func(x):
        return 0 if x < threshold else x

    # Vectorize the function
    vectorized_func = np.vectorize(threshold_func)

    # Apply the vectorized function to the input array
    return vectorized_func(arr).astype(np.uint8)


# Example usage
if __name__ == "__main__":
    # Create a sample 2D array
    sample_array = np.array([[50, 150, 200], [80, 120, 90], [300, 40, 110]])

    # Specify a threshold
    threshold_value = 600

    # Apply the function with the specified threshold
    modified_array = set_elements_below_threshold(sample_array, threshold_value)

    print("Original Array:")
    print(sample_array)
    print("\nModified Array with threshold", threshold_value, ":")
    print(modified_array)

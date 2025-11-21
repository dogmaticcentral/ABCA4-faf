import numpy as np
from PIL import Image


def gradient_by_mod8_x(path):
    # Load image as grayscale float
    img = Image.open(path).convert("L")
    arr = np.asarray(img, dtype=np.float32)

    # Compute horizontal gradient magnitude
    # Shape becomes (H, W-1)
    grad = np.abs(arr[:, 1:] - arr[:, :-1])

    # Group by x-index mod 8
    H, Wm1 = grad.shape
    groups = {k: [] for k in range(8)}

    for x in range(Wm1):
        k = x % 8
        groups[k].append(grad[:, x])

    # Compute average gradient per group
    avg_per_group = {}
    for k in range(8):
        if groups[k]:
            stacked = np.vstack(groups[k])
            avg_per_group[k] = round(float(stacked.mean()),3)
        else:
            avg_per_group[k] = None

    return avg_per_group


def outliers(indict) -> dict:
    values = list(indict.values())

    # Using Z-score (typically outlier if |z| > 3)
    mean = np.mean(values)
    std = np.std(values)
    return {k: round(float(z),1) for k, v in indict.items() if (z:=abs(v - mean) / std) > 2}

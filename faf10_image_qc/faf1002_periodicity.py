#! /usr/bin/env python3
import numpy as np
from PIL import Image
from scipy.fft import fft2, fftshift
import matplotlib.pyplot as plt

from faf05_image_qc.qc_utils.stat_utils import gradient_by_mod8_x, outliers


def detect_periodic_components(path, peak_threshold=3.0):
    # Load image and convert to grayscale float
    img = Image.open(path).convert("L")
    arr = np.asarray(img, dtype=np.float32)

    # Compute 2D FFT
    f = fft2(arr)
    fshift = fftshift(f)
    magnitude = np.abs(fshift)

    # Take log magnitude to control dynamic range
    logmag = np.log1p(magnitude)

    # Compute mean spectrum along axes
    # We’ll analyze frequencies separately along x and y.
    spectrum_x = logmag.mean(axis=0)
    spectrum_y = logmag.mean(axis=1)

    # Function to find unusually strong spikes
    def find_peaks(spec, axis_name):
        avg = np.mean(spec)
        std = np.std(spec)
        threshold = avg + peak_threshold * std
        peaks = np.where(spec > threshold)[0]
        if len(peaks) > 0:
            print(f"Strong periodic components along {axis_name}: {peaks.tolist()}")
        else:
            print(f"No strong periodic components detected along {axis_name}.")

    find_peaks(spectrum_x, "x-axis")
    find_peaks(spectrum_y, "y-axis")

    # Optional visualization
    plt.figure(figsize=(12,5))
    plt.subplot(1,2,1)
    plt.title("Spectrum (X-axis)")
    plt.plot(spectrum_x)

    plt.subplot(1,2,2)
    plt.title("Spectrum (Y-axis)")
    plt.plot(spectrum_y)
    plt.tight_layout()
    plt.show()


# Example usage:
# result = gradient_by_mod8_x("your_image.tif")
# print(result)


def main():
    imgpath = "/media/ivana/portable/abca4/faf/all/Torpedo_Tornado/OS/TT_OS_10_0.tiff"
    imgpath = "/media/ivana/portable/abca4/faf/controls/Control_6/OD/C6_OD_34_8.tiff"
    # detect_periodic_components(imgpath)
    result = gradient_by_mod8_x(imgpath)
    print(result)
    print(outliers(result))

if __name__ == "__main__":
    main()


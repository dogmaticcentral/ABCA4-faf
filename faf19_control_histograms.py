#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from utils.utils import shrug
from faf00_settings import SCORE_PARAMS


"""
Find the difference in intensity distributions in the inner an the outer ellipse for
the control images.
"""


def main():
    # check if the diff in maxima stored in settings
    # if yes, warn and return
    if gc := SCORE_PARAMS.get("gradient_correction"):
        shrug(f"SCORE_PARAMS in faf00_settings already defines gradient_correction as {gc}.")
        exit()

    # otherwise
    # for all control cases
    # create outer ellipse histogram and store in the scratch space - this can be done using faf17_roi_histograms
    # here w will just check if the histograms are preesnt
    # read in the inner ellipse histograms
    # print the avg location of maximum in the outer and in the inner ellipse
    # store in some meta-info table
    pass


#################################
if __name__ == "__main__":
    main()

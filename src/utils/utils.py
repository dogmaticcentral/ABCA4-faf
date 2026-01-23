_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

import os
from pathlib import Path

import numpy as np
from colorama import Fore, Style


def comfort(msg):
    print(Fore.GREEN  + "\t" + msg  + Style.RESET_ALL)


def is_nonempty_file(filepath: str | Path):
    filepath = Path(filepath)
    return filepath.exists() and filepath.is_file() and filepath.stat().st_size > 0


def is_runnable(filepath: str | Path):
    filepath = Path(filepath)
    return filepath.exists() and filepath.is_file() and os.access(filepath, os.X_OK)


def scream(msg):
    print(Fore.RED + "\t" + msg  + Style.RESET_ALL)


def shrug(msg):
    print(Fore.YELLOW + "\t" + msg  + Style.RESET_ALL)


def read_simple_hist(hist_path) -> list[int]:
    with open(hist_path, "r") as inf:
        histogram = [int(count) for line in inf if (count := line.strip())]
    if len(histogram) != 256:
        raise Exception(f"the length of hist in {hist_path} is not the expected 256")
    return histogram


def histogram_max(hist_path: Path | str) -> int:
    return int(np.argmax(read_simple_hist(hist_path)))

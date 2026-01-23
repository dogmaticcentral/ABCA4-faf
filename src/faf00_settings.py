
"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from peewee import Proxy

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent
WORK_DIR = Path("/home/ivana/scratch/abca4_faf")

DEBUG = True

RECOGNIZED_ENGINES = ["peewee.sqlite", "peewee.mysql", "peewee.postgres"]
DATABASES = {
    "mysql": {
        "ENGINE": "peewee.mysql",
        "DB_NAME": "abca4_faf",
        "USER": "abca4",
        "PASSWORD": os.getenv("MARIADB_PASSWD"),
        "HOST": os.getenv("MARIADB_HOST"),
        "PORT": int(os.getenv("MARIADB_PORT")),
    },
    "postgres": {
        "ENGINE": "peewee.postgres",
        "DB_NAME": "abca4_faf",
        "USER": "abca4",
        "PASSWORD": os.getenv("POSTGRES_PASSWD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": int(os.getenv("POSTGRES_PORT")),
    },
    "sqlite": {
        "ENGINE": "peewee.sqlite",  # note that peewee can also run on top of sqlite3
        "DB_NAME": f"{WORK_DIR}/abca4_faf.sqlite",
    },
}
DATABASES["default"] = DATABASES["mysql"]

# set to empty string or None if not needed
# (soffice, https://help.libreoffice.org/latest/en-US/text/shared/guide/convertfilters.html,
# is used here to convert pptx to pdf - see utils/reports.py)
SOFFICE = "/usr/bin/soffice"

# geometry parameters used in fundus analysis
# the unit distance is the distance between the centers of optic disc and fovea
GEOMETRY = {
    "disc_radius": 1 / 3,
    "fovea_radius": 1 / 9,
    "ellipse_radii": (2, 1),
    "outer_ellipse_radii": (3, 2),
    "cropping_radii": (3, 2),
}

SCORE_PARAMS = {
    "white_pixel_weight": 1,
    "black_pixel_weight": 10,
    "gradient_correction": 15
}

# this is pewee c**p that I am not sure where to put
global_db_proxy = Proxy()

USE_AUTO: bool = True








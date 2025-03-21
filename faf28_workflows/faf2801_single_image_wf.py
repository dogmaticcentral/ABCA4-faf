#! /usr/bin/env python

# there should be other ways to silence the gawdawful logging system Prefect introduces,
# but they do not seem to work

from pathlib import Path
from datetime import datetime
from sys import argv
from typing import List

import luigi
from luigi import Target
import peewee
from faf05_img_sanity_checks import check_images
from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect

# Disable Prefect's output capture
import sys
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__


class CleanError(RuntimeError):
    """Clean exception for controlled failures"""
    def __init__(self, message: str):
        super().__init__(message)
        # Shorten traceback by limiting __traceback__ depth
        self.__traceback__ = None  # Completely hides traceback (use cautiously)


class InputImage(luigi.Target):
    def __init__(self, path):
        super().__init__(path)
        self.path = path


class ImageSanityTask(luigi.Task):
    def requires(self):
        return [
            InputImage('image_in.png'),
            InputImage('annotation_in.png')
        ]

    def run(self):
        try:
            db = db_connect()
            filter_condition: peewee.Expression = FafImage.image_path == str(self.image_path)
            if not check_images(filter_condition):
                # Raise custom error for controlled failure
                raise CleanError(f"Sanity check failed for: {self.image_path}")
            db.close()

        except CleanError as e:
            # logger.error("Controlled failure in processing3: %s", e)
            raise  # Still required to block downstream tasks

        except Exception as e:
            # logger.exception("Unexpected error occurred")  # Full traceback
            raise  # Preserve standard behavior for unexpected errors


def main():
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <image path>")
        print(f"Note: for this workflow to work, the image must already be registered in the database.")
        exit(1)
    luigi.build([ImageSanityTask(argv[1])], local_scheduler=True)


if __name__ == "__main__":
    main()


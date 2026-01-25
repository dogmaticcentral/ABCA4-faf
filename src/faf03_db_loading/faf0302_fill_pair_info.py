#!/usr/bin/env python3

from typing import List, Tuple
import argparse

from models.abca4_faf_models import FafImage, ImagePair
from utils.db_utils import db_connect
from faf00_settings import global_db_proxy


def find_matching_pairs(dry_run: bool = False) -> None:
    """Find and store image pairs where paths differ only by OD/OS."""

    # Get all right eye images (OD)
    right_images = FafImage.select().where(FafImage.eye == 'OD')

    pairs_to_create: List[Tuple[int, int]] = []

    for right_img in right_images:
        # Derive expected left eye path
        expected_left_path = right_img.image_path.replace('OD', 'OS')

        # Find matching left eye image
        try:
            left_img = FafImage.get(
                (FafImage.image_path == expected_left_path) &
                (FafImage.eye == 'OS')
            )

            # Check if pair already exists
            existing = ImagePair.select().where(
                (ImagePair.left_eye_image_id == left_img.id) &
                (ImagePair.right_eye_image_id == right_img.id)
            ).exists()

            if not existing:
                pairs_to_create.append((left_img.id, right_img.id))
                print(f"Pair found: L={left_img.image_path} R={right_img.image_path}")

        except FafImage.DoesNotExist:
            continue

    if dry_run:
        print(f"\n[DRY RUN] Would create {len(pairs_to_create)} pairs")
    else:
        # Bulk insert pairs
        if pairs_to_create:
            ImagePair.insert_many([
                {'left_eye_image_id': left_id, 'right_eye_image_id': right_id}
                for left_id, right_id in pairs_to_create
            ]).execute()
            print(f"\nCreated {len(pairs_to_create)} new pairs")
        else:
            print("\nNo new pairs to create")


def main() -> None:
    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)
    parser = argparse.ArgumentParser(description='Find and store image pairs, if the names match.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print pairs without storing them')
    args = parser.parse_args()

    find_matching_pairs(dry_run=args.dry_run)
    
    if not db.is_closed():
        db.close()

if __name__ == '__main__':
    main()

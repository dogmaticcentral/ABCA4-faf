#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
import sys
import pandas as pd
from pathlib import Path
from sys import argv, stderr

from faf03_db_loading.faf0301_load_image_info import parse_device, parse_boolean

# Add parent directory to path to import local modules
sys.path.insert(0, "../..")

from utils.db_utils import db_connect
from models.abca4_faf_models import Case, FafImage
from utils.utils import is_nonempty_file

def arg_parse() -> Path:
    if len(argv) < 2 or argv[1] in ["-h", "--help"]:
        print(f"\nUsage: {argv[0]} <path to the input xlsx file>")
        print("\tThe table must contain 'Alias', 'Age', 'Eye', 'Machine', and 'Dilation' columns.")
        print()
        exit()

    infile_path = Path(argv[1])
    if not is_nonempty_file(infile_path):
        print(f"{infile_path} does not seem to be a non-empty file. Is the path ok?", file=stderr)
        exit(1)
    return infile_path


def main():
    infile_path = arg_parse()
    
    try:
        df = pd.read_excel(infile_path)
    except Exception as e:
        print(f"Error reading excel file: {e}", file=stderr)
        exit(1)

    required_columns = ["Alias", "Age", "Eye", "Machine", "Dilation"]
    if not set(required_columns).issubset(df.columns):
        print(f"Input file must contain columns: {', '.join(required_columns)}", file=stderr)
        missing = set(required_columns) - set(df.columns)
        print(f"Missing: {missing}", file=stderr)
        exit(1)

    db = db_connect()
    
    updated_count = 0
    errors_count = 0

    for index, row in df.iterrows():
        alias = row['Alias']
        age = row['Age']
        eye = row['Eye']
        machine_raw = row['Machine']
        dilation_raw = row['Dilation']

        # Parse Logic
        device_enum = parse_device(machine_raw)
        dilated_bool = parse_boolean(dilation_raw)

        if device_enum is None:
            print(f"Row {index+2}: Uninterpretable Machine value '{machine_raw}' for {alias}. Skipping.", file=stderr)
            errors_count += 1
            continue
        
        if dilated_bool is None:
            print(f"Row {index+2}: Uninterpretable Dilation value '{dilation_raw}' for {alias}. Skipping.", file=stderr)
            errors_count += 1
            continue

        try:
            # Find the image
            # We join with Case to find by alias, and match eye
            query = (FafImage
                     .select()
                     .join(Case)
                     .where(
                         (Case.alias == alias) &
                         (FafImage.eye == eye)
                     ))
            
            candidates = list(query)
            matched_image = None
            
            for img in candidates:
                if img.age_acquired is not None:
                    if round(img.age_acquired, 1) == age:
                        matched_image = img
                        break
            
            if matched_image:
                matched_image.device = device_enum
                matched_image.dilated = dilated_bool
                matched_image.save()
                updated_count += 1
                # print(f"Updated {alias} {eye} {age}: Device={device_enum.value}, Dilated={dilated_bool}")
            else:
                print(f"Row {index+2}: No matching FafImage found for Alias='{alias}', Eye='{eye}', Age={age} (rounded).", file=stderr)
                errors_count += 1

        except Exception as e:
            raise Exception(e)
            # print(f"Row {index+2}: Error processing row: {e}", file=stderr)
            # errors_count += 1

    print(f"Processing complete.")
    print(f"Updated: {updated_count} rows.")
    print(f"Errors/Skipped: {errors_count} rows.")

    db.close()

if __name__ == "__main__":
    main()

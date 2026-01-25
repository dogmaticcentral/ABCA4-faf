#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from models.abca4_faf_models import Case, FafImage, ImagePair
from utils.db_utils import db_connect
from faf00_settings import global_db_proxy


def main():
    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)

    for table in [Case, FafImage, ImagePair]:
        if table.table_exists():
            print(f"table {table._meta.table_name} found in {db.database}")
        else:
            print(f"creating {table._meta.table_name} in {db.database}")
            db.create_tables([table])
    
    if not db.is_closed():
        db.close()


########################
if __name__ == "__main__":
    main()

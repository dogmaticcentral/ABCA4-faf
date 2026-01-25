#!/usr/bin/env python

"""
    © 2024-2025 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

from models.abca4_faf_models import FafImage
from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect
from faf00_settings import global_db_proxy


def main():

    if global_db_proxy.obj is None:
         db = db_connect()
    else:
         db = global_db_proxy
         db.connect(reuse_if_open=True)

    query = (FafImage.select(
            FafImage.case_id,
            FafImage.age_acquired,
            FafImage.eye ).where(FafImage.usable == True))

    outf = open("images.tsv", "w")
    for qry_return in query:
        if qry_return.case_id.is_control: continue
        tokens = [qry_return.case_id.alias, qry_return.age_acquired, qry_return.eye]
        print("\t".join([str(t) for t in tokens]), file=outf)
    outf.close()

    if not db.is_closed():
        db.close()


########################
if __name__ == "__main__":
    main()

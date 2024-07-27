#!/usr/bin/env python
import os
import sys
sys.path.insert(0, "..")


from utils.db_utils import db_connect
from models.abca4_faf_models import FafImage


def rename_db_entry(ctrl_path, oldname, newname):
    oldpath = f"{ctrl_path}/{oldname}.tiff"
    faf_image_object_list = FafImage.select().where(FafImage.image_path==oldpath)
    if len(faf_image_object_list) > 1:
        print(f"bloop bloop {oldpath}")
        exit()
    if not faf_image_object_list  or len(faf_image_object_list) < 1:
        print(f"{oldpath} not found")
        return

    faf_id = faf_image_object_list[0].id
    base, eye, age, age_frac = newname.split("_")
    age = float(f"{age}.{age_frac}")
    update = {
        "age_acquired": age,
        "image_path":  f"{ctrl_path}/{newname}.tiff"
    }
    print(faf_id, update)
    FafImage.update(**update).where(FafImage.id == faf_id).execute()


def rename_files(dir_path, oldname, newname):

    for extension in ["hull.png"]:
        old_fnm = f"{dir_path}/{oldname}.{extension}"
        new_fnm = f"{dir_path}/{newname}.{extension}"
        if not os.path.exists(old_fnm):
            print(f"{old_fnm} not found")
            exit()
        print(f"{old_fnm}      {new_fnm}")
        os.rename(old_fnm, new_fnm)


def main():
    db = db_connect()  # this creates db proxy in globals space (that's why we do not use db explicitly)
    # home = "/storage/imaging/abca4_faf/controls"
    home = "/home/ivana/scratch/abca4_faf"
    inf  = open("renaming_table.txt")
    for line in inf:
        fields = line.strip().split()
        if len(fields) < 3: continue
        (oldname, newname, size) = fields
        base, person_idx, eye, visit_idx = oldname.split("_")
        scratch_path = f"{home}/{base}_{person_idx}/hulls"
        rename_files(scratch_path, oldname, newname)
        # ctrl_path =  f"{home}/{base}_{person_idx}/{eye}"
        # rename_db_entry(ctrl_path, oldname, newname)

    db.close()


########################
if __name__ == "__main__":
    main()


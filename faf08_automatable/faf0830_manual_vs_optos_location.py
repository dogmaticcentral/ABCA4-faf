#! /usr/bin/env python3

from pathlib import Path

import pandas as pd

import pandas as pd
from playhouse.shortcuts import model_to_dict
import sys
sys.path.insert(0, '..')
from models.abca4_faf_models import FafImage
from utils.conventions import construct_workfile_path
from utils.db_utils import db_connect
from utils.fundus_geometry import disc_macula_distance, macula_disc_angle
from utils.image_utils import svg2png


def main():

    df = pd.read_csv("../optos_fovea.tsv", delimiter="\t")
    db = db_connect()
    outf = open("fovea_estimates.tsv", "w")
    outline = ["alias", 'age', 'eye', "optos_fovea_x", "optos_fovea_y",
               "ivana_fovea_x", "ivana_fovea_y",
               "fovea_diff_x (%)", "fovea_diff_y (%)", "optos fovea confidence"]
    print("\t".join(outline), file=outf)
    for faf_img in FafImage.select().where(FafImage.usable == True):
        alias = faf_img.case_id.alias
        if "control" in alias.lower(): continue

        macula_center = (faf_img.macula_x/faf_img.width, faf_img.macula_y/faf_img.height)

        age = faf_img.age_acquired
        eye = faf_img.eye
        outline = [alias, age, eye]

        outline.extend([round(p, 3) for p in macula_center])

        selection = (df['alias'] == alias) & (df['eye'] == eye) & (df['image acquired (age, yrs)'] == age)
        optos_x, optos_y = [round(float(p)/4000, 3) for p in (df[selection]['Optos Fovea Location'].values[0]).split('\\')]
        outline.extend([optos_x, optos_y])

        # relative difference
        relative_err = [abs(optos_x-macula_center[0])/optos_x, abs(optos_y-macula_center[1])/optos_y]
        outline.extend([round(100*p, 0) for p in relative_err])

        outline.append( round(df[selection]['Optos Fovea Confidence'].values[0], 2))
        print("\t".join([str(i) for i in outline]), file=outf)

    outf.close()
    db.close()


########################
if __name__ == "__main__":
    main()


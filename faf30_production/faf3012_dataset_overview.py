#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""
from statistics import mean, median

import pandas as pd

from faf00_settings import USE_AUTO
from utils.db_utils import db_connect
from models.abca4_results import Score


def rows_from_db() -> list[dict]:
    rows = []
    for score in Score.select():
        faf_img = score.faf_image_id
        case = faf_img.case_id
        if 'control' in case.alias.lower(): continue
        rows.append({'alias': case.alias,
                     'image acquired': faf_img.age_acquired,
                     'eye': faf_img.eye,
                     'score': round(score.pixel_score_auto, 0) if USE_AUTO else round(score.pixel_score, 0)})
    return rows


def convert_to_pandas(rows):
    df = pd.DataFrame()
    for row in rows:
        new_record = pd.DataFrame([row])
        df = pd.concat([df, new_record], ignore_index=True)
    df.sort_values(by=["alias", 'image acquired'], inplace=True)
    return df


def output_spreadsheet(df):
    # we need the multiindex to merge cells in the output
    df_ind = df.set_index(['alias', 'image acquired', 'eye'])
    df_ind.to_excel("test.xlsx", merge_cells=True)


def summarize_info(df):

    # df.groupby('alias')['image acquired'].count() is a series
    img_series = df.groupby('alias')['image acquired'].count()
    min_images = img_series.min()
    max_images = img_series.max()
    med_images = img_series.median()

    # avg_imgs_per_patient = df.groupby('alias')['image acquired'].count().mean()

    df_list = df.drop(columns=['eye', 'score']).drop_duplicates().set_index('alias').groupby("alias")['image acquired'].apply(list)
    interval_lengths = []
    first_visits = []
    years_followed = []

    number_of_timepoints = 0
    for lst in df_list:
        # print(lst, len(lst))
        timepoints_per_patient = len(lst)
        number_of_timepoints += timepoints_per_patient
        age0 = lst[0]
        first_visits.append(age0)
        years_followed.append(lst[-1] - age0)
        interval_lengths.extend([round(age - age0, 1) for age in lst[1:]])

    # print(interval_lengths)
    med_intv = median(interval_lengths)
    min_intv = min(interval_lengths)
    max_intv = max(interval_lengths)

    min_first_visit = min(first_visits)
    max_first_visit = max(first_visits)
    med_first_visit = median(first_visits)

    med_yrs = median(years_followed)
    min_yrs = min(years_followed)
    max_yrs = max(years_followed)

    outstr = f"""
    We included images from {number_of_timepoints} visits. 
    A total of {min_images}-{max_images} images (median {med_images:.0f}) 
    spanning {min_yrs:.1f}-{max_yrs:.1f} (median {med_yrs:.1f}) were obtained in each patient. The first of these was obtained 
    at a median age of {med_first_visit:.1f} years (range {min_first_visit:.1f}–{max_first_visit:.1f}). 
    The median interval between follow-up visits was {med_intv:.1f} (range {min_intv:.1f}–{max_intv:.1f}).    
    """
    print(outstr)

def main():

    # get the score info from the database
    db = db_connect()
    rows = rows_from_db()
    db.close()

    df = convert_to_pandas(rows)
    output_spreadsheet(df)
    summarize_info(df)

########################
if __name__ == "__main__":
    main()

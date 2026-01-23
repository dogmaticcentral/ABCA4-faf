#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""

import matplotlib.pyplot as plt
import pandas as pd
import peewee

from faf00_settings import USE_AUTO, DATABASES
from models.abca4_faf_models import FafImage
from utils.db_utils import db_connect
from utils.utils import shrug


def sort_out_score(od_pixel_score, os_pixel_score, pair_imgs, use_auto=False) -> str:
    # not sure how to make this prettier while sticking to peewee
    right_eye_index = 0 if FafImage.get_by_id(pair_imgs[0]).eye == "OD" else 1
    left_eye_index  = 1 - right_eye_index
    score = "pixel_score_auto" if use_auto else "pixel_score"
    scores_od = FafImage.get_by_id(pair_imgs[right_eye_index]).scores
    scores_os = FafImage.get_by_id(pair_imgs[left_eye_index]).scores
    if scores_od and scores_os:
        od_pixel_score.append(getattr(scores_od[0], score))
        os_pixel_score.append(getattr(scores_os[0], score))
        return 'ok'
    else:
        shrug(f"some sores not available for the image pair with db indices {pair_imgs}")
        return 'fail'


def paired_eye_scores(controls=False) -> dict:
    [alias, age, haplotype_tested, time_from_onset, od_pixel_score, os_pixel_score] = [[] for _ in range(6)]

    # SQL: select case_id, age_acquired, group_concat(id separator ", ")
    # as img_ids from faf_images group by case_id, age_acquired \G
    # I could not find how to pass the separator to peewees GROUP_CONCAT, but "," is the default
    we_are_using_postgres = DATABASES["default"]["ENGINE"] == 'peewee.postgres'
    query = FafImage.select(
        FafImage.case_id,
        FafImage.age_acquired,
        peewee.fn.array_agg(FafImage.id).alias("img_ids") if we_are_using_postgres
        else peewee.fn.GROUP_CONCAT(FafImage.id).alias("img_ids"),
    ).group_by(FafImage.case_id, FafImage.age_acquired)

    for faf_img in query:
        if not controls and faf_img.case_id.is_control:
            continue
        if controls and not faf_img.case_id.is_control:
            continue
        if isinstance(faf_img.img_ids, int):
            continue  # this one is actually missing its mate

        pair_imgs = faf_img.img_ids if we_are_using_postgres else faf_img.img_ids.split(",")
        if len(pair_imgs) != 2: continue
        if sort_out_score(od_pixel_score, os_pixel_score, pair_imgs, USE_AUTO) != "ok": continue

        age_image_acquired = faf_img.age_acquired
        onset = faf_img.case_id.onset_age
        if age_image_acquired is None or onset is None:
            time_from_onset.append(-0.5)
        else:
            time_from_onset.append(age_image_acquired - onset)
        age.append(age_image_acquired)
        haplotype_tested.append(faf_img.case_id.haplotype_tested)
        alias.append(faf_img.case_id.alias)

    return {
        "alias": alias,
        "age": age,
        "haplotype_tested": haplotype_tested,
        "time_from_onset": time_from_onset,
        "od_pixel_score": od_pixel_score,
        "os_pixel_score": os_pixel_score,
    }


def plot_os_vs_od(df_cases: pd.DataFrame, title="OS vs OD score"):

    bigfont = 26
    smallfont = 20
    ticklabelfont = 16

    fig, ax1 = plt.subplots(1, 1)

    fig.suptitle(title, fontsize=bigfont)

    if not df_cases["haplotype_tested"].empty:
        marker = ["o" if h else "x" for h in df_cases["haplotype_tested"]]
        color = [
            "mediumblue" if h else "royalblue" for h in df_cases["haplotype_tested"]
        ]
    else:
        marker = ["o"] * len(df_cases["pixel_score"])
        color = ["mediumblue"] * len(df_cases["pixel_score"])

    maxval = max(df_cases["od_pixel_score"].max(), df_cases["os_pixel_score"].max())
    minval = min(df_cases["od_pixel_score"].min(), df_cases["os_pixel_score"].min())
    # this is a hack to make the 10^3 tickmark and lable show:
    if maxval < 1000 and maxval/1000 > 0.5: maxval = 1000
    ax1.tick_params(which="major", labelsize=ticklabelfont)
    ax1.set_xlim([minval * 0.9, maxval * 1.1])
    ax1.set_ylim([minval * 0.9, maxval * 1.1])
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.plot(
        [0, 1], [0, 1], transform=ax1.transAxes, linestyle="dotted", color="gray"
    )  # diagonal
    ax1.set_xlabel("OD score", fontsize=smallfont)
    ax1.set_ylabel("OS score", fontsize=smallfont)
    for i in range(len(df_cases["od_pixel_score"])):
        ax1.scatter(
            df_cases["od_pixel_score"][i],
            df_cases["os_pixel_score"][i],
            marker=marker[i],
            color=color[i],
        )
        ratio = df_cases["od_pixel_score"][i] / df_cases["os_pixel_score"][i]
        if ratio < 0.8 or ratio > 1.5:
            al = df_cases["alias"][i]
            ag = df_cases["age"][i]
            odp = df_cases["od_pixel_score"][i]
            osp = df_cases["os_pixel_score"][i]
            print(f"{al:30s} {ag:2.0f} {odp:3.0f} {osp:3.0f}   {ratio:.1f}")
    plt.show()


def main():
    db = db_connect()
    ret_dict = paired_eye_scores()
    df_cases = pd.DataFrame.from_dict(ret_dict)
    ret_dict = paired_eye_scores(controls=True)
    df_controls = pd.DataFrame.from_dict(ret_dict)

    title = "OS/OD score consistency"
    plot_os_vs_od(df_cases, title=title)
    db.close()


########################
if __name__ == "__main__":
    main()

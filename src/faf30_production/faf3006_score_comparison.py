#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
from statistics import mean

import matplotlib.pyplot as plt
import peewee

from faf00_settings import USE_AUTO
from models.abca4_faf_models import FafImage
from models.abca4_results import Score
from utils.db_utils import db_connect


def paired_roi_scores():
    # it looks liek this does not work in peewee
    # query = Score.select().where(Score.faf_image_id.case_id.alias == "Pearl Picnic")
    query = Score.select()
    score_elliptic = []
    score_other = []
    for score in query:
        if score.faf_image_id.case_id.is_control is False:
            continue
        if USE_AUTO:
            if score.pixel_score_auto is None:
                continue
            score_other.append(score.pixel_score_auto)
        else:
            score_other.append(score.pixel_score_peripapillary)
        score_elliptic.append(score.pixel_score)

    return score_elliptic, score_other


def plot_other_vs_elliptic_scatter(score_elliptic, score_other, title="OS vs OD score"):

    bigfont = 26
    smallfont = 20
    ticklabelfont = 16

    fig, ax1 = plt.subplots(1, 1)

    fig.suptitle(title, fontsize=bigfont)

    maxval = max(score_elliptic + score_other)
    minval = min(score_elliptic + score_other)
    ax1.tick_params(which="major", labelsize=ticklabelfont)
    ax1.set_xlim([minval * 0.9, maxval * 1.1])
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.plot(
        [0, 1], [0, 1], transform=ax1.transAxes, linestyle="dotted", color="gray"
    )  # diagonal
    if USE_AUTO:
        ax1.set_xlabel("Score manual", fontsize=smallfont)
        ax1.set_ylabel("Score auto", fontsize=smallfont)
    else:
        ax1.set_xlabel("Score in elliptic ROI", fontsize=smallfont)
        ax1.set_ylabel("Score in peripapillary ROI", fontsize=smallfont)

    ax1.scatter(score_elliptic, score_other)
    plt.show()


def paired_eye_scores(controls=False):

    # SQL: select case_id, age_acquired, group_concat(id separator ", ")
    # as img_ids from faf_images group by case_id, age_acquired \G
    # I could not find how to pass the separator to peewees GROUP_CONCAT, but "," is the default
    if USE_AUTO:
        query = FafImage.select(
            FafImage.case_id,
            FafImage.age_acquired,
            peewee.fn.GROUP_CONCAT(FafImage.id).alias("img_ids"),
        ).where(FafImage.clean_view==True
        ).group_by(FafImage.case_id, FafImage.age_acquired)

    else:
        query = FafImage.select(
            FafImage.case_id,
            FafImage.age_acquired,
            peewee.fn.GROUP_CONCAT(FafImage.id).alias("img_ids"),
        ).group_by(FafImage.case_id, FafImage.age_acquired)

    aliases = []
    avg_scores = {}
    avg_scores_other = {}
    haplotype_tested = {}

    for faf_img in query:
        if not controls and faf_img.case_id.is_control:
            continue
        if controls and not faf_img.case_id.is_control:
            continue
        if isinstance(faf_img.img_ids, int):
            continue  # this one is actually missing its mate

        pair_imgs = faf_img.img_ids.split(",")
        alias = faf_img.case_id.alias
        if alias not in aliases:
            aliases.append(faf_img.case_id.alias)
            avg_scores[alias] = []
            avg_scores_other[alias] = []
            haplotype_tested[alias] = faf_img.case_id.haplotype_tested

        if USE_AUTO:
            avg_score_other = mean(
                FafImage.get_by_id(pair_imgs[i]).scores[0].pixel_score_auto
                for i in range(len(pair_imgs))
            )
        else:
            avg_score_other = mean(
                FafImage.get_by_id(pair_imgs[i]).scores[0].pixel_score_peripapillary
                for i in range(len(pair_imgs))
            )
        avg_score = mean(
            FafImage.get_by_id(pair_imgs[i]).scores[0].pixel_score
            for i in range(len(pair_imgs))
        )

        avg_scores[alias].append(avg_score)
        avg_scores_other[alias].append(avg_score_other)

    return avg_scores, avg_scores_other, haplotype_tested


def score_sort(avg_score, avg_score_pp):
    sorted_indices = sorted(range(len(avg_score)), key=lambda i: avg_score[i])
    sorted_score = [avg_score[i] for i in sorted_indices]
    sorted_score_pp = [avg_score_pp[i] for i in sorted_indices]
    return sorted_score, sorted_score_pp


def plot_individual_cases(avg_scores, avg_scores_pp, haplotype_tested, title="blah"):
    bigfont = 26
    smallfont = 20
    ticklabelfont = 16

    fig, ax1 = plt.subplots(1, 1)

    fig.suptitle(title, fontsize=bigfont)

    minval = 1
    maxval = 1000
    ax1.tick_params(which="major", labelsize=ticklabelfont)
    ax1.set_xlim([minval * 0.9, maxval * 1.1])
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.plot(
        [0, 1], [0, 1], transform=ax1.transAxes, linestyle="dotted", color="gray"
    )  # diagonal
    if USE_AUTO:
        ax1.set_xlabel("Score manual", fontsize=smallfont)
        ax1.set_ylabel("Score auto", fontsize=smallfont)
    else:
        ax1.set_xlabel("Score in elliptic ROI", fontsize=smallfont)
        ax1.set_ylabel("Score in peripapillary ROI", fontsize=smallfont)

    for alias in avg_scores.keys():
        marker = "o" if haplotype_tested[alias] else "x"
        # ax1.plot(avg_scores[alias],  avg_scores_pp[alias], marker=marker )
        ax1.scatter(avg_scores[alias], avg_scores_pp[alias], marker=marker)
    plt.show()


def main():
    db = db_connect()

    # scatterplot
    score_elliptic, score_other = paired_roi_scores()
    title = (
        "Score manual vs auto" if USE_AUTO else "Score in elliptic vs peripapillary ROI"
    )
    plot_other_vs_elliptic_scatter(score_elliptic, score_other, title=title)

    # average over eye, and plot for individual patients
    avg_scores, avg_scores_other, haplotype_tested = paired_eye_scores()
    for alias in avg_scores.keys():
        avg_scores[alias], avg_scores_other[alias] = score_sort(
            avg_scores[alias], avg_scores_other[alias]
        )
    plot_individual_cases(avg_scores, avg_scores_other, haplotype_tested)

    db.close()


########################
if __name__ == "__main__":
    main()

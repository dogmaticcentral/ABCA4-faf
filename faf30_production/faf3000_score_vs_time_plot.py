#!/usr/bin/env python

"""
    © 2024 Ivana Mihalek ivana.mihalek@gmail.com

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/

    The License is noncommercial - you may not use this material for commercial purposes.

"""

import math
from random import sample

import pandas as pd
from statistics import mean

import peewee
from sys import argv

import matplotlib.pyplot as plt
import matplotlib.ticker
import scipy.stats as stats

from models.abca4_faf_models import FafImage
from models.abca4_results import Score, PlaygroundScore
from models.abca4_special_tables import FAF123Label
from utils.db_utils import db_connect
from faf00_settings import DATABASES, USE_AUTO


def marker_n_color(df, basecolor, faf123=None):
    if df["haplotype_tested"].empty:  # these are controls
        marker = ["o"] * len(df["pixel_score"])
        color  = ["orange"] * len(df["pixel_score"])
    else:
        marker = ["o" if h else "x" for h in df["haplotype_tested"]]
        if "faf123_label" not in df.columns or df["faf123_label"].empty:
            color = [basecolor if h else "royalblue" for h in df["haplotype_tested"]]
        else:  # we have FAF1, 2, 3 phenotype labels
            label_color = [basecolor, 'green', 'yellow', 'red']
            color = [label_color[f] for f in df["faf123_label"]]
    return marker, color


def scatter(ax, df, timeframe, basecolor, faf123=None):
    marker, color = marker_n_color(df, basecolor, faf123)
    for i in range(len(df[timeframe])):
        ax.scatter(df[timeframe][i], df["pixel_score"][i], marker=marker[i], color=color[i])


def connect(ax, df, timeframe, basecolor, faf123=None):
    # the timeframe here is time_form_onset or age - I need to coma up with a different name
    for alias in df['alias'].unique():
        sub_frame = df.loc[df['alias'] == alias].reset_index()
        if len(sub_frame) < 2: continue
        ax.plot(sub_frame[timeframe], sub_frame['pixel_score'])
        scatter(ax, sub_frame, timeframe, basecolor, faf123)


def plot_score_vs_age(df_cases: pd.DataFrame, df_controls: pd.DataFrame, title: str = "",
                      logscale=False, show_longitudinal=False, faf123=None):

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, gridspec_kw={"width_ratios": [2, 2, 1]}, sharey="row")
    fig.set_size_inches(10, 5)
    bigfont = 26
    smallfont = 20
    ticklabelfont = 16
    # share the secondary axes
    fig.suptitle(title, fontsize=bigfont)

    drawing_callable = connect if show_longitudinal else scatter

    ##############################################################
    # AGE PLOT
    ax1.tick_params(axis="both", which="major", labelsize=ticklabelfont)
    ax1.set_xlim([df_cases["age"].min() * 0.9, df_cases["age"].max() * 1.1])
    ax1.set_xlabel("Age (yrs)", fontsize=smallfont)
    ax1.set_ylabel("    Phenotype \nseverity score S", fontsize=smallfont, labelpad=10)

    if logscale:
        ax1.set_ylim([48, 1200])
        ax1.set_yscale("log")
        # ax1.set_yticks((50, 500))
        ax1.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax1.get_yaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())

    drawing_callable(ax1, df_cases, 'age', 'mediumblue', faf123)

    ##############################################################
    # TIME FROM ONSET PLOT
    ax2.tick_params(axis="x", which="major", labelsize=ticklabelfont)
    ax2.set_xlim(
        [
            df_cases["time_from_onset"].min() * 0.9,
            df_cases["time_from_onset"].max() * 1.1,
        ]
    )
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_xlabel("Time from\nsymptom onset (yrs)", fontsize=smallfont, labelpad=10)
    if logscale:
        # ax2.set_ylim([48, 1200])
        ax2.set_yscale("log")
        # ax2.set_yticks((50, 500))
        ax2.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax2.get_yaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())

    drawing_callable(ax2, df_cases, 'time_from_onset', 'mediumblue', faf123)

    ##############################################################
    # CONTROLS PLOT
    ax3.tick_params(axis="x", which="major", labelsize=ticklabelfont)
    ax3.set_xlim([df_controls["age"].min() * 0.9, df_controls["age"].max() * 1.1])
    ax3.set_ylim(ax1.get_ylim())
    ax3.set_xlabel("Controls:\nage (yrs)", fontsize=smallfont, labelpad=10)
    # ax3.set_ylabel('control: phenotype severity score', fontsize=smallfont)
    if logscale:
        ax3.set_yscale("log")
        # ax3.set_yticks((50, 500))
        ax3.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax3.get_yaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())

    drawing_callable(ax3, df_controls, 'age', 'orange')

    plt.tight_layout()
    # plt.show()
    fnm = "score_vs_time.png"
    if USE_AUTO: fnm = "auto_" + fnm
    if "average" in title: fnm = "avg_" + fnm
    if logscale: fnm = "log_" + fnm
    plt.savefig(fnm)
    print(f"figure written to {fnm}")


def img_pair_avg_score(faf_img_ids, roi, exercise):
    # there better be only one score for image id
    if exercise is None:
        if roi == "pp":
            img_scores = [FafImage.get_by_id(img_id).scores[0].pixel_score.peripapillary for img_id in faf_img_ids]
        else:
            if USE_AUTO:
                img_scores = [FafImage.get_by_id(img_id).scores[0].pixel_score_auto for img_id in faf_img_ids]
            else:
                img_scores = [FafImage.get_by_id(img_id).scores[0].pixel_score for img_id in faf_img_ids]
    else:
        if exercise == "white":
            img_scores = [FafImage.get_by_id(img_id).playground_scores[0].pixel_score_white for img_id in faf_img_ids]
        elif exercise == "black":
            img_scores = [FafImage.get_by_id(img_id).playground_scores[0].pixel_score_black for img_id in faf_img_ids]
        elif exercise == "1":
            img_scores = [FafImage.get_by_id(img_id).playground_scores[0].pixel_score_1 for img_id in faf_img_ids]
        elif exercise == "5":
            img_scores = [FafImage.get_by_id(img_id).playground_scores[0].pixel_score_5 for img_id in faf_img_ids]
        elif exercise == "15":
            img_scores = [FafImage.get_by_id(img_id).playground_scores[0].pixel_score_15 for img_id in faf_img_ids]
        else:
            raise Exception(f"Unrecognized exercise score: {exercise}")

    return mean(img_scores)


def average_eye_scores(roi="elliptic", exercise=None, controls=False) -> dict:
    [alias, age, haplotype_tested, time_from_onset, pixel_score] = [[], [], [], [], []]
    # SQL: select case_id, age_acquired, group_concat(id separator ", ")
    # as img_ids from faf_images group by case_id, age_acquired \G
    # I could not find how to pass the separator to peewees GROUP_CONCAT, but "," is the default
    # in postgres, I could not get this to work, to be closer to the mysql solution
    # # peewee.fn.string_agg(peewee.fn.cast(FafImage.id, 'TEXT')).alias('img_ids'),
    we_are_using_postgres = DATABASES["default"]["ENGINE"] == 'peewee.postgres'

    if USE_AUTO:
        query = FafImage.select(
            FafImage.case_id,
            FafImage.age_acquired,
            peewee.fn.array_agg(FafImage.id).alias("img_ids") if we_are_using_postgres
            else peewee.fn.GROUP_CONCAT(FafImage.id).alias("img_ids"),
        ).where(FafImage.clean_view == True
        ).group_by(FafImage.case_id, FafImage.age_acquired)

    else:
        query = FafImage.select(
            FafImage.case_id,
            FafImage.age_acquired,
            peewee.fn.array_agg(FafImage.id).alias("img_ids") if we_are_using_postgres
            else peewee.fn.GROUP_CONCAT(FafImage.id).alias("img_ids"),
        ).group_by(FafImage.case_id, FafImage.age_acquired)
    # print(query.sql())
    # exit()
    timepoints = 0
    for faf_img in query:
        if not controls and faf_img.case_id.is_control: continue
        if controls and not faf_img.case_id.is_control: continue
        timepoints += 1
        alias.append(faf_img.case_id.alias)
        if isinstance(faf_img.img_ids, int):
            pair_imgs = [faf_img.img_ids]  # this one is actually missing its pair
        else:
            pair_imgs = faf_img.img_ids if we_are_using_postgres else faf_img.img_ids.split(",")

        avg_score = img_pair_avg_score(pair_imgs, roi, exercise)
        pixel_score.append(avg_score)
        age_image_acquired = faf_img.age_acquired
        onset = faf_img.case_id.onset_age
        if age_image_acquired is None or onset is None:
            time_from_onset.append(-0.5)
        else:
            time_from_onset.append(age_image_acquired - onset)
        age.append(age_image_acquired)
        haplotype_tested.append(faf_img.case_id.haplotype_tested)

    print(f"total timepoints when averaging {'controls' if controls else ''}: {timepoints}")
    return {
        "alias": alias,
        "age": age,
        "haplotype_tested": haplotype_tested,
        "time_from_onset": time_from_onset,
        "pixel_score": pixel_score,
    }


def which_score(score, roi, exercise) -> float:
    if exercise is None:
        if roi == "pp":
            return score.pixel_score_peripapillary
        else:
            if USE_AUTO:
                return score.pixel_score_auto
            else:
                return score.pixel_score
    else:
        if exercise == "white":
            return score.pixel_score_white
        elif exercise == "black":
            return score.pixel_score_blackrevised_supplement.pdf
        elif exercise == "1":
            return score.pixel_score_1
        elif exercise == "5":
            return score.pixel_score_5
        elif exercise == "15":
            return score.pixel_score_15
        else:
            raise Exception(f"Unrecognized exercise score: {exercise}")


def individual_eye_scores(roi="elliptic", exercise=None, controls=False, faf123=False) -> dict:

    [age, haplotype_tested, time_from_onset, pixel_score, faf123_labels] = [[], [], [], [], []]
    timepoints = 0
    if exercise is None:
        score_selector = Score.select()
    else:
        score_selector = PlaygroundScore.select()
    for score in score_selector:
        case = score.faf_image_id.case_id
        if not controls and score.faf_image_id.case_id.is_control:
            continue
        if controls and not score.faf_image_id.case_id.is_control:
            continue
        if USE_AUTO and not score.faf_image_id.clean_view: continue
        timepoints += 1
        # print(score, score.faf_image_id, score.pixel_score, score.faf_image_id.age_acquired)
        # print("\t", case.alias, case.onset_age)
        age_image_acquired = score.faf_image_id.age_acquired
        onset = case.onset_age
        if age_image_acquired is None or onset is None:
            time_from_onset.append(-0.5)
        else:
            time_from_onset.append(age_image_acquired - onset)
        age.append(age_image_acquired)
        pixel_score.append(which_score(score, roi, exercise))
        haplotype_tested.append(case.haplotype_tested)

        if not faf123:
            faf123_labels.append(0)
            continue
        query = FAF123Label.select().where(FAF123Label.faf_image_id == score.faf_image_id)
        faf123_label = [flb.label  for flb in query]
        if len(faf123_label) == 0:
            # note this means that I may not have the faf123
            # for the cases I am not interested in (or for the controls)
            faf123_labels.append(0)
        elif len(faf123_label) > 1:
            raise Exception(f"More than one label found for {case.alias}, {age_image_acquired}")
        else:
            faf123_labels.append(faf123_label[0])

    return {
        "age": age,
        "haplotype_tested": haplotype_tested,
        "time_from_onset": time_from_onset,
        "pixel_score": pixel_score,
        "faf123_label": faf123_labels
    }


def report_stats(x, y, labels: list, outf=None, latex=False) -> tuple[float, float]:
    spearman = stats.spearmanr(x, y)
    pearson  = stats.pearsonr(x, y)
    print(f"{labels}:   Spearman correlation {spearman.statistic * 100:.1f}%     p-val: {spearman.pvalue:.2e}")
    print(f"{labels}:   Pearson  correlation {pearson.statistic*100:.1f}%     p-val: {pearson.pvalue:.2e}")
    if outf:
        separator = " & " if latex else "\t"
        end = "\\\\ \\hline \n" if latex else "\n"
        pct = "\\%" if latex else "%"
        sp_out = ["Spearman", f"{spearman.statistic * 100:.1f}{pct}", f"{spearman.pvalue:.2e}"]
        print(separator.join(labels + sp_out), file=outf, end=end)
        pear_out = ["Pearson", f"{pearson.statistic * 100:.1f}{pct}", f"{pearson.pvalue:.2e}"]
        print(separator.join(labels + pear_out), file=outf, end=end)
    return spearman, pearson


def improvized_arg_parser() -> tuple:
    if len(argv) > 1 and argv[1] in ["-h", "--help"]:
        print(f"{argv[0]} [-h/--help] | [-a/--avg] [-p/--peripapillary] [-l/--latex] [--exercise-<type>] [-f/--color_by_faf123]")
        exit()
    average = len({"-a", "--avg"}.intersection(argv)) > 0
    latex = len({"-l", "--latex"}.intersection(argv)) > 0
    roi = "pp" if {"-p", "--peripapillary"}.intersection(argv) else "elliptic"
    faf123 = {"-f", "--color_by_faf123"}.intersection(argv)
    exercise = None
    for exrcise_type in ["black", "white", "1", "5", "15"]:
        if f"--exercise-{exrcise_type}" in argv:
            exercise = exrcise_type

    return average, latex, roi, faf123, exercise


def construct_title(base, exercise, average) -> str:
    title = base
    if exercise:
        if exercise == "white":
            title += ", light component only"
        elif exercise == "black":
            title += ", dark component only"
        else:
            title += f", dark/light relative weight: {exercise}"
    if average:
        title += ", average over OD and OS"

    return title


def main():

    (average, latex, roi, faf123, exercise) = improvized_arg_parser()

    db = db_connect()  # this initializes global proxy
    if average:
        ret_dict = average_eye_scores(roi=roi, exercise=exercise)
        df_cases = pd.DataFrame.from_dict(ret_dict)
        ret_dict = average_eye_scores(roi=roi, exercise=exercise, controls=True)
        df_controls = pd.DataFrame.from_dict(ret_dict)
    else:
        ret_dict = individual_eye_scores(roi=roi, exercise=exercise, faf123=faf123)
        df_cases = pd.DataFrame.from_dict(ret_dict)
        ret_dict = individual_eye_scores(roi=roi, exercise=exercise, controls=True)
        df_controls = pd.DataFrame.from_dict(ret_dict)
    db.close()

    print(f"number of points {len(df_cases)}")

    filtered_df = df_cases.loc[df_cases["haplotype_tested"]]
    print(f"number of points with the haplotype tested {len(filtered_df)}")

    out_fnm = "stats.tex" if latex else "stats.tsv"
    with open(out_fnm, "w") as outf:
        separator = " & " if latex else "\t"
        print(
            separator.join(
                [
                    "scale",
                    "time frame",
                    "phased only",
                    "statistic",
                    "correlation",
                    "p-value",
                ]
            ),
            file=outf,
        )
        if latex: print("\\\\ \\hline \\hline",  file=outf)
        print("\nLINEAR SCALE")
        report_stats(df_cases["age"], df_cases["pixel_score"], ["linear", "age", "no"], outf, latex=latex)
        report_stats(
            df_cases["time_from_onset"],
            df_cases["pixel_score"],
            ["linear", "onset", "no"],
            outf,
            latex=latex
        )
        report_stats(
            filtered_df["age"],
            filtered_df["pixel_score"],
            ["linear", "age", "yes"],
            outf,
            latex=latex
        )
        report_stats(
            filtered_df["time_from_onset"],
            filtered_df["pixel_score"],
            ["linear", "onset", "yes"],
            outf,
            latex=latex

        )
        print("\nLOG SCALE")
        logscore = [math.log(s) for s in df_cases["pixel_score"]]
        report_stats(df_cases["age"], logscore, ["log", "age", "no"], outf, latex=latex)
        report_stats(df_cases["time_from_onset"], logscore, ["log", "onset", "no"], outf, latex=latex)
        logscore = [math.log(s) for s in filtered_df["pixel_score"]]
        report_stats(filtered_df["age"], logscore, ["log", "age", "yes"], outf, latex=latex)
        report_stats(filtered_df["time_from_onset"], logscore, ["log", "onset", "yes"], outf, latex=latex)

    title = construct_title(f"Score vs time", exercise, average)
    plot_score_vs_age(df_cases, df_controls, title=title, show_longitudinal=True)

    title =  construct_title(f"Log score vs time", exercise, average)
    plot_score_vs_age(df_cases, df_controls, title=title, logscale=True, show_longitudinal=True)


########################
if __name__ == "__main__":
    main()

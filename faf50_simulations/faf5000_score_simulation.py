#! /usr/bin/env python3
from math import sin, pi
from statistics import mean
import matplotlib.pyplot as plt
import matplotlib.ticker


def intensity(t):
    if t < 0:
        print("we cannot go to the past with this toy model")
        exit()
    if t <= 1.5:
        return sin(t * pi)
    return -1


def intensity_score(t):
    if t < 0:
        print("we cannot go to the past with this toy model")
        exit()
    if t <= 1.0:
        return sin(t * pi)
    if t <= 1.5:
        return 2 * (1 - sin(t * pi))
    return 4.0

blue_colors = [
    "#082f49",
    "#0c4a6e",
    "#075985",
    "#0369a1",
    "#0284c7",
    "#0ea5e9",
    "#38bdf8",
    "#7dd3fc",
    "#7dd3fc",
    "#7dd3fc",
]

yellow_colors = [
    '#c2410c',
    '#ea580c',
    '#ca8a04',
    '#eab308',
    '#facc15',
    '#fde047',
    '#fdba74',
    '#fef08a',
    '#fef08a',
    '#fef08a',
]

bigfont = 26
smallfont = 20
ticklabelfont = 16


def plot(trajectories, avg_trajectory, intensities, avg_intensity):

    fig, (ax1, ax2) = plt.subplots(1, 2)
    plt.subplots_adjust(left=0.1, bottom=0.2)

    fig.set_size_inches(12, 5)
    ax1.set_ylim(-1.2, 4.2)
    ax2.set_ylim(-1.2, 4.2)
    ax1.tick_params(axis='both', which='major', labelsize=ticklabelfont)
    ax2.tick_params(axis='both', which='major', labelsize=ticklabelfont)

    ax1.set_xlabel('Time, arbitrary units', fontsize=smallfont, labelpad=10)
    ax1.set_ylabel('Model intensity \n measured from the bg value', fontsize=smallfont, labelpad=2)
    for idx, intensity in enumerate(intensities):
        params = {'color': yellow_colors[idx % len(yellow_colors)]}
        if idx == len(intensities)//2: params['label'] = "individual pixels"
        ax1.plot(intensity, **params)
    ax1.plot(avg_intensity, color="green", linewidth=5, label="average")
    ax1.legend(loc="upper left", fontsize=ticklabelfont)

    ax2.set_xlabel('Time, arbitrary units', fontsize=smallfont, labelpad=10)
    ax2.set_ylabel('Intensity score', fontsize=smallfont, labelpad=2)
    for idx, trajectory in enumerate(trajectories):
        params = {'color': blue_colors[idx % len(yellow_colors)]}
        if idx == len(intensities)//2: params['label'] = "individual pixels"
        ax2.plot(trajectory, **params)
    ax2.plot(avg_trajectory, color="red", linewidth=5, label="average")
    ax2.legend(loc="upper left", fontsize=ticklabelfont)

    plt.show()


def main():
    t_max = 2.0
    number_of_timepoints = 1000
    time_step = t_max / number_of_timepoints
    score_trajectories = []
    intensities = []
    for starting_timepoint in range(number_of_timepoints + 1):
        intensity_trajectory = [0] * starting_timepoint
        intensity_trajectory += [
            intensity(n * time_step)
            for n in range(number_of_timepoints + 1 - starting_timepoint)
        ]
        intensities.append(intensity_trajectory)

        score_trajectory = [0] * starting_timepoint
        score_trajectory += [
            intensity_score(n * time_step)
            for n in range(number_of_timepoints + 1 - starting_timepoint)
        ]
        score_trajectories.append(score_trajectory)

    avg_intensity = [
        mean([itsty[i] for itsty in intensities]) for i in range(number_of_timepoints)
    ]
    avg_trajectory = [
        mean([t[i] for t in score_trajectories]) for i in range(number_of_timepoints)
    ]
    plot(
        score_trajectories[:: number_of_timepoints // 10],
        avg_trajectory,
        intensities[:: number_of_timepoints // 10],
        avg_intensity,
    )


if __name__ == "__main__":
    main()

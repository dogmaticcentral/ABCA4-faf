from itertools import product

import numpy as np
from faf20_pixel_score import PixelScore


def test_score2color():
    height = 3
    width  = 5
    score_matrix = np.zeros((height, width, 2))

    score_matrix[1, 1, 0] = 50
    score_matrix[1, 2, 0] = 250
    score_matrix[1, 3, 0] = 350

    score_matrix[2, 1, 1] = 50
    score_matrix[2, 2, 1] = 250
    score_matrix[2, 3, 1] = 350

    color_matrix = PixelScore.score2color(score_matrix)
    # suppress supresses the use of scientific notation - works - occasionally
    np.set_printoptions(precision=3, suppress=True, formatter={'float': '{:.0f}'.format})
    print(score_matrix)
    print("*****************")
    print(color_matrix)
    for y in range(height):
        assert all([c == 0 for c in color_matrix[y, 0, :]])
        assert all([c == 0 for c in color_matrix[y, 4, :]])

    for y in [1,2]:
        for x in [1, 2,3]:
            assert color_matrix[y, x, 3] == 255

    print()
    for y, x in product(range(height), range(width)):
        if (color_matrix[y, x, 2] < 200): continue
        print(y, x, color_matrix[y, x, 2])

    # ndarray_to_4channel_png(color_matrix, "test.png")
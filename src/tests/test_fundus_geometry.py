import pytest
from utils.fundus_geometry import fovea_disc_angle

testdata = [
    ((50, 60), (100, 60), 0, "Zero angle"),
    ((50, 60), (50, 100), 90, "90 deg angle"),
    ((50, 60), (30, 60), 180, "180 deg angle"),
    ((50, 60), (50, 30), -90, "-90 deg angle")
]


@pytest.mark.parametrize("point_a, point_b, expected, msg", testdata)
def test_disc_macula_angle(point_a, point_b, expected, msg):
    assert (fovea_disc_angle(point_a, point_b) == expected), msg


testdata_anti = [
    ((50, 60), (100, 70), 0, "Non-zero angle"),
     ((50, 60), (50, 30), 270, "270 deg reported as -90")
]


@pytest.mark.parametrize("point_a, point_b, expected, msg", testdata_anti)
def test_disc_macula_angle_anti(point_a, point_b, expected, msg):
   assert (fovea_disc_angle(point_a, point_b) != expected), msg



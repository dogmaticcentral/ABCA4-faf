_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

from utils.vector import Vector


def disc_macula_distance(disc_center, macula_center):
    return Vector.distance(Vector(disc_center), Vector(macula_center))


def macula_disc_angle(macula_center, disc_center):

    macula_to_disc =  Vector(disc_center) - Vector(macula_center)
    (r, theta) = macula_to_disc.toPolarDeg()
    return theta


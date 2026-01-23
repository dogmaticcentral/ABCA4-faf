_copyright__ = """

    Copyright 2024 Ivana Mihalek

    Licensed under Creative Commons Attribution-NonCommercial 4.0 International Public License:
    You may obtain a copy of the License at https://creativecommons.org/licenses/by-nc/4.0/
    
    The License is noncommercial - you may not use this material for commercial purposes.

"""
__license__ = "CC BY-NC 4.0"

# -*- coding: utf8 -*-

"""vector.py: A simple little Vector class. Enabling basic vector math. """
# based on the work by Sven Hecht, info@shdev.de, with some enhancements and debugging by Ivana Mihalek
import math
from math import *
from random import *


class Vector:
    def __init__(self, x=0.0, y=0.0):
        self.x: float = 0.0
        self.y: float = 0.0
        if isinstance(x, tuple) or isinstance(x, list):
            y = x[1]
            x = x[0]
        elif isinstance(x, Vector):
            y = x.y
            x = x.x

        self.set(x, y)

    @staticmethod
    def random(size=1):
        sizex = size
        sizey = size
        if isinstance(size, tuple) or isinstance(size, list):
            sizex = size[0]
            sizey = size[1]
        elif isinstance(size, Vector):
            sizex = size.x
            sizey = size.y
        return Vector(random() * sizex, random() * sizey)

    @staticmethod
    def randomUnitCircle():
        d = random() * pi
        return Vector(cos(d) * choice([1, -1]), sin(d) * choice([1, -1]))

    @staticmethod
    def distance(a, b) -> float:
        return (a - b).getLength()

    @staticmethod
    def principal_angle(v1, v2):
        argument = v1.dotproduct(v2) / (v1.getLength() * v2.getLength())
        if argument > 1.0: argument = 1.0
        # defending ourselves from -1.0000000000000002
        if argument < -1.0: argument = -1.0
        return acos(argument)

    @staticmethod
    def signed_angle(v1, v2):
        # - pi to pi
        cp   = v1.crossproduct(v2)
        sign = 1 if cp >= 0 else -1
        return sign*Vector.principal_angle(v1, v2)

    @staticmethod
    def unsigned_angle(v1, v2):
        # 0 to 2 pi
        a = Vector.signed_angle(v1, v2)
        return a if a >= 0 else 2*pi + a

    @staticmethod
    def angleDeg(v1, v2):
        return Vector.principal_angle(v1, v2) * 180.0 / pi

    def rotated(self, origin, angle):
        new_coords = self - origin
        (r, theta) = new_coords.toPolar()
        rotated = Vector(r*cos(theta+angle), r*sin(theta+angle))
        return rotated + origin

    def set(self, x: float, y: float):
        self.x = x
        self.y = y

    def toPolar(self):
        r = self.getLength()
        x = self.x
        y = self.y
        # atan2 (not atan) provides the correct quadrant with respect to the unit circle for your angle
        theta = atan2(y, x) if abs(x) > 0 else (math.pi/2 if y > 0 else -math.pi/2)
        return (r, theta)

    def toPolarDeg(self):
        (r, theta) = self.toPolar()
        return (r, theta*180/math.pi)

    def toArr(self):
        return [self.x, self.y]

    def toTuple(self):
        return (self.x, self.y)

    def toIntTuple(self):
        return (int(self.x), int(self.y))

    def toInt(self):
        return Vector(int(self.x), int(self.y))

    def toIntArr(self):
        return self.toInt().toArr()

    def get_normalized(self):
        norm = self.getLength()
        if norm > 0:
            # [IM: this operation is not defined]
            # return self / self.getLength()
            return Vector(self.x/norm, self.y/norm)
        else:
            return Vector(0, 0)

    def crossproduct(self, other):
        if isinstance(other, Vector):
            return self.x * other.y -  self.y * other.x
        elif isinstance(other, tuple) or isinstance(other, list):
            return self.x * other[1] - self.y * other[0]
        else:
            return NotImplemented


    def dotproduct(self, other):
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y
        elif isinstance(other, tuple) or isinstance(other, list):
            return self.x * other[0] + self.y * other[1]
        else:
            return NotImplemented

    def orthogonal_unit(self, handedness='r'):
        if handedness not in ['r', 'l']:
            print(f"unrecognized handedness: {handedness}")
            exit(1)

        norm = math.sqrt(self.x**2 + self.y**2)
        if self.x**2 - self.y**2 > 0:
            if handedness == 'r':
                (a, b) = (self.y, -self.x)
            else:
                (a, b) = (-self.y, self.x)
        else:
            if handedness == 'r':
                (a, b) = (-self.y, self.x)
            else:
                (a, b) = (self.y, -self.x)

        return Vector(a/norm, b/norm)

    # this should be operator overloading
    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        elif isinstance(other, tuple) or isinstance(other, list):
            return Vector(self.x + other[0], self.y + other[1])
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x + other, self.y + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        if isinstance(other, tuple) or isinstance(other, list):
            return Vector(self.x - other[0], self.y - other[1])
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x - other, self.y - other)
        else:
            return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, Vector):
            return Vector(other.x - self.x, other.y - self.y)
        elif isinstance(other, tuple) or isinstance(other, list):
            return Vector(other[0] - self.x, other[1] - self.y)
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(other - self.x, other - self.y)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x * other.x, self.y * other.y)
        elif isinstance(other, tuple) or isinstance(other, list):
            return Vector(self.x * other[0], self.y * other[1])
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x * other, self.y * other)
        else:
            return NotImplemented

    # In Python 3.x, you need to overload the __floordiv__ and __truediv__ operators, not the __div__ operator.
    # The former corresponds to the // operation (returns an integer) and the latter to / (returns a float).
    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x / other.x, self.y / other.y)
        elif isinstance(other, tuple) or isinstance(other, list):
            return Vector(self.x / other[0], self.y / other[1])
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(self.x / other, self.y / other)
        else:
            return NotImplemented

    def __floordiv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x // other.x, self.y // other.y)
        elif isinstance(other, tuple) or isinstance(other, list):
            return Vector(self.x // other[0], self.y // other[1])
        elif isinstance(other, int):
            return Vector(self.x // other, self.y // other)
        else:
            return NotImplemented

    def __rdiv__(self, other):
        if isinstance(other, Vector):
            return Vector(other.x / self.x, other.y / self.y)
        elif isinstance(other, tuple) or isinstance(other, list):
            return Vector(other[0] / self.x, other[1] / self.y)
        elif isinstance(other, int) or isinstance(other, float):
            return Vector(other / self.x, other / self.y)
        else:
            return NotImplemented

    def __pow__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector(self.x ** other, self.y ** other)
        else:
            return NotImplemented

    def __iadd__(self, other):
        if isinstance(other, Vector):
            self.x += other.x
            self.y += other.y
            return self
        elif isinstance(other, tuple) or isinstance(other, list):
            self.x += other[0]
            self.y += other[1]
            return self
        elif isinstance(other, int) or isinstance(other, float):
            self.x += other
            self.y += other
            return self
        else:
            return NotImplemented

    def __isub__(self, other):
        if isinstance(other, Vector):
            self.x -= other.x
            self.y -= other.y
            return self
        elif isinstance(other, tuple) or isinstance(other, list):
            self.x -= other[0]
            self.y -= other[1]
            return self
        elif isinstance(other, int) or isinstance(other, float):
            self.x -= other
            self.y -= other
            return self
        else:
            return NotImplemented

    def __imul__(self, other):
        if isinstance(other, Vector):
            self.x *= other.x
            self.y *= other.y
            return self
        elif isinstance(other, tuple) or isinstance(other, list):
            self.x *= other[0]
            self.y *= other[1]
            return self
        elif isinstance(other, int) or isinstance(other, float):
            self.x *= other
            self.y *= other
            return self
        else:
            return NotImplemented

    def __idiv__(self, other):
        if isinstance(other, Vector):
            self.x /= other.x
            self.y /= other.y
            return self
        elif isinstance(other, tuple) or isinstance(other, list):
            self.x /= other[0]
            self.y /= other[1]
            return self
        elif isinstance(other, int) or isinstance(other, float):
            self.x /= other
            self.y /= other
            return self
        else:
            return NotImplemented

    def __ipow__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            self.x **= other
            self.y **= other
            return self
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, Vector):
            return self.x == other.x and self.y == other.y
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Vector):
            return self.x != other.x or self.y != other.y
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Vector):
            return self.getLength() > other.getLength()
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Vector):
            return self.getLength() >= other.getLength()
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Vector):
            return self.getLength() < other.getLength()
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, Vector):
            return self.getLength() <= other.getLength()
        else:
            return NotImplemented

    def __len__(self):
        return int(sqrt(self.x ** 2 + self.y ** 2))

    def getLength(self):
        return sqrt(self.x ** 2 + self.y ** 2)

    def __getitem__(self, key):
        if key == "x" or key == "X" or key == 0 or key == "0":
            return self.x
        elif key == "y" or key == "Y" or key == 1 or key == "1":
            return self.y

    def __str__(self):
        return f"[x: {self.x:.3f}, y: {self.y:.3f}]"

    def __repr__(self):
        return f"[x: {self.x:.3f}, y: {self.y:.3f}]"

    def __neg__(self):
        return Vector(-self.x, -self.y)


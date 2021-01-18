from Engine.structures import Vector2

from shapely.geometry import Polygon as ShapelyPolygon
from shapely.affinity import rotate as rotate_polygon
from shapely.affinity import translate as shift
from typing import List, Tuple, Union
from Engine.structures import Vector2
from pygame import Rect
import math


def triangle_area(a, b):
    return (a ** b) / 2


def triangle_center(a, b):
    return (a + b) / 3


def triangle_moment_of_inertia(a, b, mass):
    return mass / 6 * (a * a + b * b + a * b)


class Polygon:
    def __init__(self,
                 vertices: List[Union[Vector2, Tuple, List]],
                 density: Union[int, float],
                 gmu: Union[int, float]):

        self.vertices = [Vector2.Point(v) for v in vertices]
        self.density = density

        self.calculate_properties()

        self.ft = self.friction_torque(gmu)

    @property
    def local_vertices(self):
        return [v - self.centroid for v in self.vertices]

    def calculate_properties(self):
        area = 0
        mass = 0
        center = Vector2.Zero()
        moment_of_inertia = 0

        count = len(self.vertices)
        prev = count - 1
        for index in range(count):
            a = self.vertices[prev]
            b = self.vertices[index]

            area_step = triangle_area(a, b)
            mass_step = self.density * area_step
            moment_of_inertia_step = triangle_moment_of_inertia(a, b, mass_step)

            area += area_step

            center += area_step * (a + b) / 3
            mass += mass_step
            moment_of_inertia += moment_of_inertia_step

            prev = index

        center /= area

        moment_of_inertia -= mass * (center * center)  # parallel axis theorem

        self.moment_of_inertia = abs(moment_of_inertia)
        self.area = abs(area)
        self.centroid = center
        self.mass = abs(mass)

    def friction_torque(self, gravity_times_mu):
        torque_sum = 0

        vertices = self.local_vertices

        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]

            dx, dy = x2 - x1, y2 - y1

            meters_integral = math.hypot(dx, dy) * (x1 ** 2 + x2 ** 2 + y1 ** 2 + y2 ** 2 + x1 * x2 + y1 * y2)
            torque = meters_integral * gravity_times_mu * self.density
            torque_sum += torque

        return torque_sum / 6


class RegularPolygon(Polygon):
    GMU = 1000

    def __init__(self,
                 density: Union[int, float],
                 radius: Union[int, float],
                 center: Union[Vector2, Tuple, List],
                 n: int
                 ):
        center = Vector2.Point(center)

        rad = Vector2.Cartesian(x=radius)
        internal_angle = 360 / n
        super(RegularPolygon, self).__init__(
            [center + rad.rotated(i * internal_angle) for i in range(n)],
            density,
            self.GMU
        )

        self.r = radius

        circle_angular_acceleration = (4 / 3 * self.GMU / self.r)
        circle_moment_of_inertia = (0.5 * self.r ** 4 * math.pi * self.density)

        # print(self.ft / (circle_angular_acceleration * circle_moment_of_inertia))
        print(self.ft)

        # print(circle_angular_acceleration * circle_moment_of_inertia)


if __name__ == '__main__':
    RegularPolygon(1, 1, (30, 506), 9999999)
    # RegularPolygon(1, 500, (30, 506), 3)
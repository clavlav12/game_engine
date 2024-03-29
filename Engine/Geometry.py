from shapely.geometry import Polygon as ShapelyPolygon
from shapely.affinity import rotate as rotate_polygon
from shapely.affinity import translate as shift
from typing import List, Tuple, Union
from Engine.structures import Vector2
from pygame import Rect
import math


def triangle_area(a, b):
    """Triangle area by two points and origin"""
    return (a ** b) / 2


def triangle_center(a, b):
    """Triangle center by two points and origin"""
    return (a + b) / 3


def triangle_moment_of_inertia(a, b, mass):
    """Triangle moment of inertia by two points, mass and origin"""
    return mass / 6 * (a * a + b * b + a * b)


class Polygon:
    def __init__(self,
                 vertices: List[Union[Vector2, Tuple, List]],
                 density: Union[int, float],
                 *, gravity_times_mu=None):

        self.world_vertices = [Vector2.Point(v) for v in vertices]
        self.density = density

        shapely_vertices = [v.values for v in self.world_vertices]
        self.shapely_polygon = ShapelyPolygon(shapely_vertices)
        self.reference_shapely_polygon = ShapelyPolygon(shapely_vertices)

        self.calculate_properties()
        self.update_rect()

        if gravity_times_mu is not None:
            self.ft = self.friction_torque(gravity_times_mu)

    @property
    def local_vertices(self):
        return [v - self.centroid for v in self.world_vertices]

    def update_centroid(self, new_centroid: Vector2):
        """Shifts the polygon by giving it a new com position"""
        c = self.shapely_polygon.centroid
        offset = new_centroid - (c.x, c.y)
        self.shapely_polygon = shift(self.shapely_polygon, offset.x, offset.y)
        self.update_vertices()
        self.centroid = new_centroid

    def rotate_and_move(self, new_angle: Union[int, float], centroid, radians=False):
        """Rotates and shift the polygon at the same time"""
        self.shapely_polygon = rotate_polygon(self.reference_shapely_polygon, new_angle, 'centroid', radians)
        self.update_centroid(centroid)

    def update_vertices(self):
        """Update vertices to match to shapely's"""
        self.world_vertices = [Vector2.Point(v) for v in self.shapely_polygon.exterior.coords]
        self.update_rect()

    def update_rect(self):
        """Updates polygon's hitbox"""
        bounds = self.shapely_polygon.bounds  # Returns a (minx, miny, maxx, maxy) that bounds the object.
        self.rect = Rect(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])

    def intersection(self, other):
        """Returns the intersection area between self and other"""
        assert isinstance(other, Polygon)
        return tuple(self.shapely_polygon.intersection(other.shapely_polygon).coords)

    def calculate_properties(self):
        """Calculate important properties such as area, mass, centroid and moment of inertia"""
        area = 0
        mass = 0
        center = Vector2.Zero()
        moment_of_inertia = 0

        count = len(self.world_vertices)
        prev = count - 1
        for index in range(count):
            a = self.world_vertices[prev]
            b = self.world_vertices[index]

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
        """Calculates the torque done by horizontal friction (Currently the formula is broken)"""
        torque_sum = 0

        vertices = self.local_vertices

        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]

            dx, dy = x2 - x1, y2 - y1

            meters_integral = math.hypot(dx, dy) * (x1 ** 2 + x2 ** 2 + y1 ** 2 + y2 ** 2 + abs(x1 * x2) + abs(y1 * y2))
            torque = meters_integral * gravity_times_mu * self.density
            torque_sum += torque

        return torque_sum / 6


if __name__ == '__main__':
    p1 = [
        Vector2.Polar(1, 0) + Vector2.Cartesian(500, 200),
        Vector2.Polar(1, 120) + Vector2.Cartesian(500, 200),
        Vector2.Polar(1, 240) + Vector2.Cartesian(500, 200),
        ]

    # p1 = [[550.00000, 500.00000], [475.00000, 543.30127], [475.00000, 456.69873]]

    my_poly = Polygon(p1, 1)
    print(my_poly.centroid)
    print(my_poly.shapely_polygon.centroid)
    print(my_poly.rect.center)

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
    return mass / 6 * (a*a + b*b + a*b)


class Polygon:

    def __init__(self,
                 vertices: List[Union[Vector2, Tuple, List]],
                 density: Union[int, float]):

        self.world_vertices = [Vector2.Point(v) for v in vertices]
        self.density = density

        shapely_vertices = [v.values for v in self.world_vertices]
        self.shapely_polygon = ShapelyPolygon(shapely_vertices)
        self.reference_shapely_polygon = ShapelyPolygon(shapely_vertices)

        self.calculate_properties()
        self.update_rect()

        self.ft = self.friction_torque(1000)

    @property
    def local_vertices(self):
        return [v - self.centroid for v in self.world_vertices]
    
    def update_centroid(self, new_centroid: Vector2):
        c = self.shapely_polygon.centroid
        offset = (c.x, c.y) - new_centroid
        self.shapely_polygon = shift(self.shapely_polygon, offset.x, offset.y)
        self.update_vertices()
        self.centroid = new_centroid

    def rotate(self, new_angle: Union[int, float], centroid, radians=False):
        self.shapely_polygon = rotate_polygon(self.reference_shapely_polygon, new_angle, 'centroid', radians)
        self.update_centroid(centroid)
        self.update_vertices()

    def update_vertices(self):
        self.world_vertices = [Vector2.Point(v) for v in self.shapely_polygon.exterior.coords]
        self.update_rect()

    def update_rect(self):
        bounds = self.shapely_polygon.bounds  # Returns a (minx, miny, maxx, maxy) that bounds the object.
        self.rect = Rect(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
        # print(self.world_vertices)

    def intersection(self, other):
        assert isinstance(other, Polygon)
        return tuple(self.shapely_polygon.intersection(other.shapely_polygon).coords)

    def calculate_properties(self):
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

    def friction_torque(self, mun):
        torque_sum = 0

        vertices = self.local_vertices
        for i in range(len(vertices)-1):
            x1, y1 = vertices[i]
            x2, y2 = vertices[i+1]
            dx, dy = x2 - x1, y2 - y1

            torque_sum += math.hypot(dx, dy) * (x1 ** 2 + x2 ** 2+ y1 **2 + y2 ** 2 + x1 * x2 + y1 * y2)

        return torque_sum / 6


if __name__ == '__main__':
    p2 = [(0, 0), (50, 0), (50, 100), (0, 100)]
    p1 = [(50, 50), (100, 50), (100, 100), (50, 100)]

    my_poly = Polygon(p1, 1)
    my_poly2 = Polygon(p2, 1)
    import time
    start = time.time()
    print(my_poly.intersection(my_poly2))
    print(time.time()-start)
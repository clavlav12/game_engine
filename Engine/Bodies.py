from Engine.structures import Vector2, DegTrigo, PrivateConstructorAccess, sub_tuples
from Engine.pygame_structures import Camera
import Engine.Geometry as Geometry
from abc import ABC, abstractmethod
from typing import Union, List, Tuple
import pygame

Number = Union[int, float]
Point = Union[List[Number], Tuple[Number, Number], Vector2]


class RotationMatrix:
    def __init__(self, angle):
        self.tl = DegTrigo.cos(angle)
        self.tr = -DegTrigo.sin(angle)
        self.bl = -self.tr
        self.br = self.tl

    def __mul__(self, other):
        """
        :param other: Vector2 to multiply by
        :return: Result of matrix multiplication
        """
        if isinstance(other, Vector2):
            return Vector2.Cartesian(
                self.tl * other.x + self.tr * other.y,
                self.bl * other.x + self.br * other.y
            )
        return NotImplemented

    def __rmul__(self, other):
        return self * other


class Body(ABC):
    EMPTY = pygame.Surface((0, 0))

    def __init__(self, vertices: List[Point], center_offset, parent_orientation: Union[int, float],
                 color=pygame.Color('blue'), brush_width=1):
        """
        :param vertices:
        :param center_offset: offset of centroid from parent's position
        :param color:
        :param brush_width:
        """
        self.vertices = vertices
        self.reference_vertices = self.vertices.copy()
        self.color = color
        self.brush_width = brush_width
        self.image: pygame.Surface = self.EMPTY
        self.center_offset = center_offset
        self.reference_orientation = parent_orientation
        # self.update_position(parent_position, parent_orientation)

    @property
    @abstractmethod
    def position(self):
        """
        :return: Body centroid
        """

    @position.setter
    @abstractmethod
    def position(self, value):
        """
        change object's vertices to match value as centroid
        :param value:
        :return:
        """

    @abstractmethod
    def get_rect(self):
        """
        :return: sprite's current hitbox
        """
        pass

    def update_position(self, parent_position: Point, parent_orientation: Union[int, float], ):
        """
        Updates position and orientation by parent position (updates orientation at the same time to save performance)
        :param parent_position: Parent sprite's position (Vector2)
        :param parent_orientation: Parent sprite's orientation (float)
        """
        matrix = RotationMatrix(parent_orientation - self.reference_orientation)

        self.position = parent_position + (self.center_offset * matrix)

        self.vertices = [self.position + (matrix * (v - self.position)) for v in self.reference_vertices]

    def update_floating_vertices(self, axis):
        """
        some objects have other kinds of vertices that change depending on the collision
        :param axis: axis of collision
        :return: vertices to use on SAT
        """
        pass

    def redraw(self, position=None):
        """
        :param position: position to blit (if not provided uses the current held position)
        """
        if position is None:
            position = (self.position - Vector2.Point(self.image.get_size()) / 2)
        position = tuple(position)
        Camera.screen.blit(self.image, position - Camera.scroller)

    def get_normals(self, other):
        """
        Generates axis to check for collision on the SAT test
        :param other: Second sprite to perform collision test with
        :return: axis to check for collision
        """
        return [(self.vertices[i + 1] - self.vertices[i]).normalized().normal()
                for i in range(len(self.vertices) - 1)]


class Line(Body):
    def __init__(self, p1: Point, p2: Point, center_offset=Vector2.Zero(), orientation=0):
        p1, p2 = Vector2.Point(p1), Vector2.Point(p2)
        super(Line, self).__init__([p1, p2], Vector2.Point(center_offset), orientation)
        self.dir = (p2 - p1).normalized()
        self.length = (p2 - p1).magnitude()

    @property
    def position(self):
        return (self.vertices[0] + self.vertices[1]) / 2

    @position.setter
    def position(self, value):
        offset = value - self.position
        for i in range(len(self.vertices)):
            self.vertices[i] += offset

    def redraw(self, _=None):
        r = self.get_rect()
        self.image = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.line(self.image, pygame.Color('white'), sub_tuples(self.vertices[0], r.topleft),
                         sub_tuples(self.vertices[1], r.topleft))
        # pygame.image.save(self.image, 'line.png')
        super(Line, self).redraw()

    def get_rect(self):
        p1, p2 = self.vertices
        min_vec = p1.min(p2)
        max_vec = p1.max(p2)

        return pygame.Rect(*min_vec, *((max_vec - min_vec).max(Vector2.Cartesian(1, 1))))


class Circle(Body):
    def __init__(self, center: Point, radius: Number, center_offset: Point = Vector2.Zero(), orientation=0):
        super(Circle, self).__init__([Vector2.Zero(), Vector2.Zero()], center_offset, orientation)
        self.radius = radius
        self.center = center
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color,
                           (self.radius, self.radius),
                           self.radius, 0)
        pygame.draw.circle(self.image, pygame.Color('black'),
                           (self.radius, self.radius),
                           self.radius, 4)

    @property
    def position(self):
        return self.center

    @position.setter
    def position(self, value: Point):
        self.center = Vector2.Point(value)

    def update_floating_vertices(self, axis):
        self.vertices[0] = self.position + axis * -self.radius
        self.vertices[1] = self.position + axis * self.radius

    def get_normals(self, other):
        if isinstance(other, Circle):
            return [(other.position - self.position).normalized()]
        return [(self.closest_vertex_to_point(other.vertices, self.position) - self.position).normalized()]

    @staticmethod
    def closest_vertex_to_point(vertices, p):
        """
        Finds the closest vertex to a point
        :param vertices: List of vertices
        :param p: point
        :return: Vertex (from the list) that is closest to point p
        """
        closest_vertex = None
        min_distance = float('inf')

        for vertex in vertices:
            distance = (p - vertex).square_magnitude()
            if distance < min_distance:
                closest_vertex = vertex.copy()
                min_distance = distance

        return closest_vertex

    def get_rect(self):
        return pygame.Rect(*(self.center - Vector2.Cartesian(self.radius, self.radius)),
                           self.radius * 2, self.radius * 2)


class Polygon(Body):
    def __init__(self,
                 vertices: List[Point],
                 center_offset: Point = Vector2.Zero(),
                 orientation=0):
        center_offset = Vector2.Point(center_offset)
        self.polygon = Geometry.Polygon(vertices, 1)

        super(Polygon, self).__init__([], center_offset, orientation)

    @property
    def vertices(self):
        return self.polygon.world_vertices

    @vertices.setter
    def vertices(self, _):
        pass

    @property
    def position(self):
        return self.polygon.centroid

    def update_position(self, parent_position: Point, parent_orientation: Union[int, float], ):
        matrix = RotationMatrix(parent_orientation - self.reference_orientation)

        new_position = parent_position + (self.center_offset * matrix)

        self.polygon.rotate_and_move(parent_orientation - self.reference_orientation, new_position)

    def redraw(self, _=None):
        self.image = pygame.Surface(tuple(self.polygon.rect.size +
                                          Vector2.Cartesian(self.brush_width, self.brush_width) * 2), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, self.color, [tuple(v - self.polygon.rect.topleft) for v in
                                                     self.polygon.world_vertices], 0
                            )
        pygame.draw.polygon(self.image, pygame.Color('black'), [tuple(v - self.polygon.rect.topleft) for v in
                                                     self.polygon.world_vertices], 4
                            )

        super(Polygon, self).redraw(self.polygon.rect.topleft)

    def get_rect(self):
        return self.polygon.rect


class CheapOBB(Body):
    def __init__(self,
                 rect,
                 orientation,
                 ):
        self.rect = rect
        super(CheapOBB, self).__init__(
            [
                self.rect.topleft,
                self.rect.topright,
                self.rect.bottomright,
                self.rect.bottomleft
            ],
            Vector2.Zero(), orientation
        )

    @property
    def position(self):
        return self.rect.center

    def update_position(self, parent_position: Point, parent_orientation: Union[int, float]):
        matrix = RotationMatrix(parent_orientation - self.reference_orientation)
        for vertex in self.vertices:
            vertex -= parent_position
            vertex *= matrix
            vertex += parent_position

    def redraw(self, _=None):
        pass

    def get_rect(self):
        v = self.vertices

        left = min(v, key=lambda x: x.x)
        top = min(v, key=lambda x: x.y)
        right = max(v, key=lambda x: x.x)
        bottom = max(v, key=lambda x: x.y)
        return pygame.Rect(
            left, top, right - left, bottom - top
        )

    def get_normals(self, other):
        return [(self.vertices[1] - self.vertices[0]).normalized(), (self.vertices[2] - self.vertices[1]).normalized()]


class AABB(Body):
    normals = [Vector2.Cartesian(x=1), Vector2.Cartesian(y=1)]

    def __init__(self, rect):
        self.rect = rect
        super(AABB, self).__init__(self.vertices, (0, 0), 0)

    @property
    def vertices(self):
        return [Vector2.Point(v) for v in
                [self.rect.topleft, self.rect.topright, self.rect.bottomright, self.rect.bottomleft]
                ]

    @vertices.setter
    def vertices(self, _):
        pass

    @property
    def position(self):
        return self.rect.center

    def update_position(self, parent_position: Point, parent_orientation: Union[int, float]):
        self.rect.center = parent_position

    def redraw(self, _=None):
        pass

    def get_rect(self):
        return self.rect

    def get_normals(self, other):
        return self.normals


class Rectangle(Polygon):
    __key = object()

    def __init__(self,
                 key,
                 vertices: List[Point],
                 center_offset: Point = Vector2.Zero(),
                 orientation: Number = 0):
        if key is not self.__key:
            raise PrivateConstructorAccess.DefaultMessage(self.__class__)

        super(Rectangle, self).__init__(vertices, center_offset, orientation)

    @classmethod
    def AxisAligned(cls,
                    center,
                    width_extent: Number,
                    height_extent: Number,
                    center_offset: Point = Vector2.Zero(),
                    orientation: Number = 0):
        width_extent = Vector2.Cartesian(x=width_extent)
        height_extent = Vector2.Cartesian(y=height_extent)

        vertices = [
            center + width_extent + height_extent,
            center - width_extent + height_extent,
            center - width_extent - height_extent,
            center + width_extent - height_extent,
        ]
        return cls(cls.__key, vertices, center_offset, orientation)

    @classmethod
    def Oriented(cls,
                 p1: Point,
                 p2: Point,
                 width: Number,
                 center_offset: Point = Vector2.Zero(),
                 orientation: Number = 0
                 ):
        vertices = [
            Vector2.Point(p1),
            Vector2.Point(p2),
            None,
            None
        ]

        edge = vertices[1] - vertices[0]
        length = edge.magnitude()
        direction = edge.normalized()
        vertices[2] = vertices[1] + direction.perpendicular() * width
        vertices[3] = vertices[2] - direction * length

        return cls(cls.__key, vertices, center_offset, orientation)

    def get_normals(self, other):
        return [(self.vertices[1] - self.vertices[0]).normalized(), (self.vertices[2] - self.vertices[1]).normalized()]


class RegularPolygon(Polygon):
    def __init__(self, center, radius, n, center_offset=Vector2.Zero(), orientation=0):
        center = Vector2.Point(center)
        rad = Vector2.Cartesian(x=radius)
        internal_angle = 360 / n

        super(RegularPolygon, self).__init__(
            [center + rad.rotated(i * internal_angle) for i in range(n)],
            center_offset,
            orientation,
        )

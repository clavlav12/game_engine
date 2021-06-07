from Engine import pygame_structures
from Engine import base_sprites
from Engine import base_control
from typing import Optional, Tuple
from Engine import structures
import pygame as pg
import math
import random

Camera = pygame_structures.Camera


class Line:
    def __init__(self, point1, point2):
        """If you start from the equation y-y1 = (y2-y1)/(x2-x1) * (x-x1) (which is the equation of the line
        defined by two points), through some manipulation you can get (y1-y2) * x + (x2-x1) * y + (x1-x2)*y1 +
        (y2-y1)*x1 = 0, and you can recognize that:
        a = y1-y2,
        b = x2-x1,
        c = (x1-x2)*y1 + (y2-y1)*x1.
        """
        self.a = point1[1] - point2[1]
        self.b = point2[0] - point1[0]
        self.c = (point1[0] - point2[0]) * point1[1] + (point2[1] - point1[1]) * point1[0]

    def distance_from_point(self, point):
        return abs(self.a * point[0] + self.b * point[1] + self.c) / math.hypot(self.a, self.b)

    def intersection_point(self, other):
        return pg.math.Vector2(
            (self.c * other.b - self.b * other.c) / (self.b * other.a - self.a * other.b),
            (self.a * other.c - self.c * other.a) / (self.b * other.a - self.a * other.b)
        )

    def draw(self, color=pg.Color('green'), width=1):
        if not self.b == 0:
            pg.draw.line(Camera.screen, color, self.get_point(0), self.get_point(Camera.screen.get_width()), width)
        else:
            pg.draw.line(Camera.screen, color, self.get_point_by_y(0), self.get_point_by_y(Camera.screen.get_height()),
                         width)

    def get_point(self, x):
        return pg.math.Vector2(
            x,
            - (self.a * x + self.c) / self.b
        )

    def get_point_by_y(self, y):
        return pg.math.Vector2(
            - (self.b * y + self.c) / self.a,
            y
        )

    def distance_from_line(self):
        """Unneeded for now"""
        pass


class RigidCube(base_sprites.ImagedRigidBody):
    def __init__(self, size, x, y):
        rect = pg.Rect(
            x - size // 2,
            y - size // 2,
            size, size
        )
        image = pg.transform.smoothscale(base_sprites.Slime.sur, [size] * 2).convert_alpha()
        super(RigidCube, self).__init__(image, rect, 500, 10 ** 2, 0)

        self.size = size
        self.generate_collision_manifold = True
        self.collision_manifold_generator = self.manifold_generator
        self.collision_manifold_generator = pygame_structures.collision_manifold.by_two_objects
        self.restitution = 0

        self.vertices_unrotated = [pg.math.Vector2(point) * 0.5 for point in (
            (size, size),
            (size, -size),
            (-size, -size),
            (-size, size))
                                   ]
        self.normals_unrotated = [pg.math.Vector2(*point) for point in (
            (1, 0),
            (0, -1),
            (-1, 0),
            (0, 1))
                                  ]

        self.restitution = 0.5
        # self.vertices_rotated = self.vertices_unrotated
        # self.normals = self.normals_unrotated
        self.rotate(self.orientation)

    def rotate(self, da):
        self.orientation += da

    @property
    def vertices_rotated(self):
        return [
            vec.rotate(-self.orientation) for vec in self.vertices_unrotated
        ]

    @property
    def normals(self):
        return [
            vec.rotate(-self.orientation) for vec in self.normals_unrotated
        ]

    @property
    def vertices(self):
        position = pg.math.Vector2(*self.com_position)
        return [vertex + position for vertex in self.vertices_rotated]

    @classmethod
    def get_support(cls, self, direction: pg.math.Vector2) -> Tuple[pg.math.Vector2, int]:
        if isinstance(self, RigidCube):
            vertices = self.vertices
        else:
            vertices = cls.aabb_to_world_vertices(self.rect)

        # for vertex in vertices:
        #     pg.draw.circle(pygame_structures.Camera.screen, pg.Color('green'), vertex, 2)

        best_projection = float('-inf')
        best_vertex = None
        best_vertex_idx = 0
        for idx, vertex in enumerate(vertices):
            projection = vertex * direction
            if projection > best_projection:
                best_vertex = pg.math.Vector2(*vertex)
                best_projection = projection
                best_vertex_idx = idx

        return best_vertex, best_vertex_idx

    @classmethod
    def find_axis_of_lease_penetration(cls, self, other) -> tuple:
        """
        :return: normal vector, penetration depth
        """
        if isinstance(self, RigidCube):
            vertices = self.vertices
            normals = self.normals
        else:
            vertices = cls.aabb_to_world_vertices(self.rect)
            normals = cls.aabb_to_noramls()

        best_distance = float('-inf')
        best_index: int = 0
        best_support = None
        best_support_index = 0

        for idx, vertex in enumerate(vertices):
            normal = normals[idx]

            support, support_index = cls.get_support(other, -1 * normal)

            penetration_distance = normal * (support - vertex)

            if penetration_distance > best_distance:
                best_distance = penetration_distance
                best_index = idx
                best_support = support
                best_support_index = support_index

        p1 = vertices[best_index]
        if best_index + 1 < len(vertices):
            p2 = vertices[best_index + 1]
        else:
            p2 = vertices[0]

        line = Line(p1, p2)

        return best_index, best_distance, line.distance_from_point(best_support), best_support_index

    @staticmethod
    def aabb_to_vertices(rect: pg.Rect):
        return [
            pg.math.Vector2(point) * 0.5 for point in (
                (rect.width, rect.height),
                (rect.width, -rect.height),
                (-rect.width, -rect.height),
                (-rect.width, rect.height))
        ]

    @staticmethod
    def aabb_to_world_vertices(rect: pg.Rect):
        return [pg.math.Vector2(*point) for point in [rect.bottomright, rect.topright, rect.topleft, rect.bottomleft]]

    @staticmethod
    def aabb_to_noramls():
        return [pg.math.Vector2(*point) for point in (
            (1, 0),
            (0, -1),
            (-1, 0),
            (0, 1))
                ]

    @staticmethod
    def no_collision(a, b):
        return pygame_structures.collision_manifold(a, b,
                                                    None, None, False, False)

    @classmethod
    def manifold_generator(cls, sprite_a, sprite_b):
        face_a_index, penetration_a, distance_a, support_point_a = cls.find_axis_of_lease_penetration(sprite_a,
                                                                                                      sprite_b)
        if penetration_a >= 0:
            return cls.no_collision(sprite_a, sprite_b)

        face_b_index, penetration_b, distance_b, support_point_b = cls.find_axis_of_lease_penetration(sprite_b,
                                                                                                      sprite_a)
        if penetration_b >= 0:
            return cls.no_collision(sprite_a, sprite_b)

        if cls.bias_greater_than(penetration_a, penetration_b):
            ref_poly = sprite_a
            inc_poly = sprite_b
            reference_index = face_a_index
            support_index_inc = support_point_a
            support_index_ref = support_point_b
            flip = False
            reference_distance = distance_a
        else:
            support_index_inc = support_point_b
            support_index_ref = support_point_a
            ref_poly = sprite_b
            inc_poly = sprite_a
            reference_index = face_b_index
            flip = True
            reference_distance = distance_b

        if isinstance(ref_poly, RigidCube):
            ref_vertices = ref_poly.vertices
            ref_normals = ref_poly.normals
        else:
            ref_vertices = cls.aabb_to_world_vertices(ref_poly.rect)
            ref_normals = cls.aabb_to_noramls()

        if isinstance(inc_poly, RigidCube):
            inc_vertices = inc_poly.vertices
        else:
            inc_vertices = cls.aabb_to_world_vertices(inc_poly.rect)

        normal = ref_normals[reference_index]

        p1 = ref_vertices[reference_index]
        p2 = ref_vertices[(reference_index + 1) % len(ref_vertices)]

        support_points = [structures.Vector2.Point(v) for v in [inc_vertices[support_index_inc]]]

        return pygame_structures.collision_manifold(
            sprite_a, sprite_b, reference_distance,
            structures.Vector2.Point(normal),
            True, False, support_points, len(support_points)
        )

    @staticmethod
    def get_position(sprite):
        if isinstance(sprite, RigidCube):
            return pg.math.Vector2(*sprite.com_position)
        elif isinstance(sprite, base_sprites.BaseSprite):
            return pg.math.Vector2(*sprite.position) + pg.math.Vector2(sprite.rect.size) / 2
        else:  # tile
            return pg.math.Vector2(*sprite.rect.center)

    @staticmethod
    def bias_greater_than(a, b):
        k_biasRelative = 0.95
        k_biasAbsolute = 0.01
        return a >= b * k_biasRelative + a * k_biasAbsolute

    def draw(self, draw_health=False):
        super(RigidCube, self).draw(draw_health)
        for vertex in self.vertices:
            pg.draw.circle(pygame_structures.Camera.screen, pg.Color('black'), vertex, 5)

    def collision(self, other):
        self.sprite_collide_func(other, collision)
        return True

    def sprite_collide_func(self, _sprite, collision):
        relative_velocity = _sprite.velocity - self.velocity
        velocity_among_normal = relative_velocity * collision.normal

        pg.draw.circle(pygame_structures.Camera.screen, pg.Color('white'), tuple(self.com_position), 10)

        if velocity_among_normal > 0:
            return

        j = -(1 + self.restitution) * velocity_among_normal
        j /= 1 / float('inf') + 1 / _sprite.mass

        impulse = j * collision.normal

        if collision.contact_count > 0:
            for point in collision.contact_points:
                if point is not None:
                    _sprite.apply_impulse(1 / _sprite.mass * impulse / collision.contact_count, point)
                    self.apply_impulse(-1 / self.mass * impulse / collision.contact_count, point)
        else:
            _sprite.apply_impulse(1 / self.mass * impulse)
            self.apply_impulse(-1 / self.mass * impulse)

        non_infinite = next(filter(lambda x: x.mass < 50000, [_sprite, self]))
        percent = 0.2
        slop = 0.01
        correction = max(collision.penetration - slop, 0.0) / (1 / non_infinite.mass) * percent * collision.normal
        _sprite.position += 1 / non_infinite.mass * correction
        _sprite.set_position()


class c2(RigidCube):
    def __init__(self, *args, **kwargs):
        super(c2, self).__init__(*args, **kwargs)
        self.mass = 999999999999999999999999999999999999999999999

    def apply_gravity(self):
        return


def main():
    W = 1000
    H = 700
    screen = pygame_structures.DisplayMods.Windowed((W, H))
    pygame_structures.Camera.init(screen, "static", None)

    sur = pg.Surface((50, 50)).convert()
    sur.fill((0, 255, 255))
    tile_list = [
        [{'id': 3} for _ in range(50)] for __ in range(50)
    ]
    size = 50
    collection = pygame_structures.TileCollection()
    for i in range(0, W // size):
        tile_list[(H - size) // size][i] = {'id': 1, 'img': sur, 'group': collection}

    pygame_structures.Map(tile_list, [], [], [], size)
    fps = 1000
    elapsed = 1 / fps
    running = True
    while running:
        events = pg.event.get()
        for event in events:
            if event.type == pg.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pg.QUIT:
                running = 0
            elif event.type == pg.KEYDOWN:
                pass
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    cube = RigidCube(50, *event.pos)
                else:
                    cube = c2(50, *event.pos)
                    pygame_structures.Camera.set_scroller_position(cube, True)

        keys = pg.key.get_pressed()
        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    main()

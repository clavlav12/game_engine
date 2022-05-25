from Engine import pygame_structures
from Engine import base_sprites
from Engine import base_control
from typing import Optional, Tuple
from Engine import structures
from Engine import Geometry

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


class Edge:
    def __init__(self, vertices, normal: pg.math.Vector2):
        c = len(vertices)
        max_projection = float('-inf')
        best_index = 0
        for i in range(c):
            projection = normal.dot(vertices[i])
            if projection > max_projection:
                max_projection = projection
                best_index = i

        v = vertices[best_index]
        v1 = vertices[(best_index + 1) % len(vertices)]
        v0 = vertices[best_index - 1]

        l = v - v1
        r = v - v0

        l.normalize()
        r.normalize()

        if r.dot(normal) <= l.dot(normal):
            self.v = v
            self.v1 = v0
            self.v2 = v

        else:
            self.v = v
            self.v1 = v
            self.v2 = v1

def draw_arrow(start, vec, lcolor=pg.Color('red'), tricolor=pg.Color('green'), trirad=3, thickness=2, scale=1):
    end = tuple(start + vec * scale)
    start = tuple(start)
    rad = math.pi/180
    pg.draw.line(pygame_structures.Camera.screen, lcolor, start, end, thickness)
    rotation = (math.atan2(start[1] - end[1], end[0] - start[0])) + math.pi/2
    pg.draw.polygon(pygame_structures.Camera.screen, tricolor, ((end[0] + trirad * math.sin(rotation),
                                                                 end[1] + trirad * math.cos(rotation)),
                                                                (end[0] + trirad * math.sin(rotation - 120*rad),
                                                                 end[1] + trirad * math.cos(rotation - 120*rad)),
                                                                (end[0] + trirad * math.sin(rotation + 120*rad),
                                                                 end[1] + trirad * math.cos(rotation + 120*rad))))

class RotatableImage:
    def __init__(self, img, init_angle, center_offset):
        self.original_img = img
        self.edited_img = img.copy()
        self.pivot = pg.math.Vector2(center_offset[0], -center_offset[1])
        self.center_offset = center_offset

        w, h = self.original_img.get_size()
        self.box = [pg.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]

        self.angle = None

        self.rotate(init_angle)
        self.angle = init_angle

    def rotate(self, angle, skip_optimisation=False):
        if not angle == self.angle or skip_optimisation:
            self.angle = angle
            self.box_rotate = box_rotate = [p.rotate(angle) for p in self.box]
            self.min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
            self.max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
            pivot_rotate = self.pivot.rotate(angle)
            self.pivot_move = pivot_rotate - self.pivot
            self.edited_img = pg.transform.rotate(self.original_img, angle)

    def blit_image(self, center_position):
        origin = (center_position[0] - self.center_offset[0] + self.min_box[0] - self.pivot_move[0],
                  center_position[1] - self.center_offset[1] - self.max_box[1] + self.pivot_move[1])
        Camera.blit(self.edited_img,
                    origin - Camera.scroller)

        # pygame.draw.rect(Camera.screen, Color('red'), r, 5)
        return self.edited_img, origin


class RigidCube(base_sprites.ImagedRigidBody):
    def __init__(self, size, x, y, density=1):
        rect = pg.Rect(
            x - size // 2,
            y - size // 2,
            size, size
        )

        image = pg.transform.smoothscale(base_sprites.Slime.sur, [size] * 2).convert_alpha()
        super(RigidCube, self).__init__(image, rect, 500, 1/12 * 500 * 2 * size ** 2, random.randrange(90))

        self.size = size
        self.generate_collision_manifold = True
        self.collision_manifold_generator = self.manifold_generator
        # self.collision_manifold_generator = pygame_structures.collision_manifold.by_two_objects
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

        self.restitution = 0
        # self.vertices_rotated = self.vertices_unrotated
        # self.normals = self.normals_unrotated
        self.real_image = RotatableImage(image, self.orientation,
                                                           (25, 25))
        polygon = Geometry.Polygon(self.vertices, density)
        self.moment_of_inertia = polygon.moment_of_inertia
        self.mass = polygon.mass

    def _update(self, _):
        super(RigidCube, self)._update(_)
        self.apply_gravity()

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
        position = pg.math.Vector2(*self.position)
        return [vertex + position for vertex in self.vertices_rotated]

    @classmethod
    def get_vertices(cls, obj):
        if isinstance(obj, RigidCube):
            return obj.vertices
        else:
            return cls.aabb_to_world_vertices(obj.rect)

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

        try:
            line = Line(p1, p2)

            return best_index, best_distance, line.distance_from_point(best_support), best_support_index
        except Exception as e:
            # print(p1, p2, vertices, self, self.                                       , self.vertices_unrotated)
            raise e

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
            # print("no coll")
            return cls.no_collision(sprite_a, sprite_b)

        face_b_index, penetration_b, distance_b, support_point_b = cls.find_axis_of_lease_penetration(sprite_b,
                                                                                                      sprite_a)
        if penetration_b >= 0:
            # print("no coll")
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

        support_points = cls.contact_points(ref_poly, inc_poly, normal)

        if support_points:
            for i in support_points:
                pg.draw.circle(Camera.screen, pg.Color('red'), i, 2)

        if not flip:
            normal *= -1

        # support_points = [inc_vertices[support_index_inc]]
        # support_points = []

        support_points = [structures.Vector2.Point(v) for v in support_points]

        # print(support_points)
        return pygame_structures.collision_manifold(
            ref_poly, inc_poly, reference_distance,
            structures.Vector2.Point(normal),
            True, False, support_points, len(support_points)
        )
    
    @classmethod
    def contact_points(cls, ref_poly, inc_poly, normal):
        ref_edge = Edge(cls.get_vertices(ref_poly), normal)
        inc_edge = Edge(cls.get_vertices(inc_poly), -normal)  # - normal?
        refv = ref_edge.v2 - ref_edge.v1 # <->
        refv = refv.normalize()

        o1 = refv.dot(ref_edge.v1)
        cp = cls.clip(inc_edge.v1, inc_edge.v2, refv, o1)
        if len(cp) < 2:
            return []

        o2 = refv.dot(ref_edge.v2)
        cp = cls.clip(cp[0], cp[1], -refv, -o2)
        if len(cp) < 2:
            return []

        refNorm = normal

        # if flip:
        #     refNorm = refNorm * -1

        max_ = refNorm.dot(ref_edge.v) # maxd??
        final = []
        if not refNorm.dot(cp[0]) < max_:
            final.append(cp[0])
        if not refNorm.dot(cp[1]) < max_:
            final.append(cp[1])

        return cp

    @staticmethod
    def clip(v1, v2, n, o):
        cp = []
        d1 = n.dot(v1) - o
        d2 = n.dot(v2) - o

        if d1 >= 0.0:
            cp.append(v1)

        if d2 >= 0.0:
            cp.append(v2)

        if d1 * d2 < 0.0:
            e = v2 - v1
            u = d1 / (d1 - d2)
            e = e * u
            e = e + v1
            cp.append(e)
        return cp

    @staticmethod
    def get_position(sprite):
        if isinstance(sprite, RigidCube):
            return pg.math.Vector2(*sprite.position)
        elif isinstance(sprite, base_sprites.BaseSprite):
            return pg.math.Vector2(*sprite.position)
        else:  # tile
            return pg.math.Vector2(*sprite.rect.center)

    @staticmethod
    def bias_greater_than(a, b):
        k_biasRelative = 0.95
        k_biasAbsolute = 0.01
        return a >= b * k_biasRelative + a * k_biasAbsolute

    def draw(self, draw_health=False):

        super(RigidCube, self).draw()
        for vertex in self.vertices:
            pg.draw.circle(pygame_structures.Camera.screen, pg.Color('black'), vertex, 5)
        # pg.draw.circle(pygame_structures.Camera.screen, pg.Color('white'), tuple(self.com_position), 10)
        # pg.draw.circle(pygame_structures.Camera.screen, pg.Color('white'), tuple(self.position), 10)
        # self.draw_rect()

    def collision(self, other):
        self.sprite_collide_func2(other, None)
        return True

    def sprite_collide_func(self, _sprite, collision):
        if not collision:
            return True

        # collision.normal *= -1
        relative_velocity = _sprite.velocity - self.velocity
        velocity_among_normal = relative_velocity * collision.tangent

        pg.draw.circle(pygame_structures.Camera.screen, pg.Color('white'), tuple(self.position), 10)

        if velocity_among_normal > 0:
            return True

        j = -(1 + self.restitution) * velocity_among_normal
        j /= 1 / float('inf') + 1 / _sprite.mass

        impulse = j * collision.tangent

        # print(impulse, velocity_among_normal)
        self.friction(_sprite, collision, j)

        if collision.contact_count > 0:
            for point in collision.contact_points:
                if point is not None:
                    _sprite.apply_impulse(1 / _sprite.mass * impulse / collision.contact_count, point)
                    self.apply_impulse(-1 / self.mass * impulse / collision.contact_count, point)
        else:
            _sprite.apply_impulse(1 / _sprite.mass * impulse)
            self.apply_impulse(-1 / self.mass * impulse)

        try:
            non_infinite = next(filter(lambda x: x.mass < 50000, [_sprite, self]))
            percent = 0.2
            slop = 0.01
            correction = max(collision.penetration - slop, 0.0) / (1 / non_infinite.mass) * percent * collision.tangent
            non_infinite.position += 1 / non_infinite.mass * correction
            non_infinite.set_position()
        except StopIteration:
            pass

    def sprite_collide_func2(self, sprite, collision):
        if not collision:
            return True

        # collision.normal *= -1
        for point in collision.contact_points:
            arm1 = point - self.position
            rot_vel1 = math.radians(self.angular_velocity) ** arm1
            close_vel1 = self.velocity + rot_vel1

            draw_arrow(
                self.position,
                close_vel1,
                scale=10
            )

            arm2 = point - sprite.position
            rot_vel2 = math.radians(sprite.angular_velocity) ** arm2
            close_vel2 = sprite.velocity + rot_vel2

            # impulse augmentation
            imp_aug1 = arm1 ** collision.tangent
            imp_aug1 = imp_aug1 * self.inv_moment_of_inertia * imp_aug1
            imp_aug2 = arm2 ** collision.tangent
            imp_aug2 = imp_aug2 * sprite.inv_moment_of_inertia * imp_aug2

            relative_velocity = close_vel1 - close_vel2

            separating_velocity = relative_velocity * collision.tangent

            if separating_velocity > 0:
                return

            new_separating_velocity = -separating_velocity * min(self.restitution, sprite.restitution)

            vel_sep_diff = new_separating_velocity - separating_velocity

            if not (self.inv_mass + sprite.inv_mass + imp_aug1 + imp_aug2):
                return

            impulse = vel_sep_diff / (self.inv_mass + sprite.inv_mass + imp_aug1 + imp_aug2)
            impulse_vector = collision.tangent * impulse
            impulse_vector /= collision.contact_count

            self.velocity += impulse_vector * self.inv_mass
            sprite.velocity += impulse_vector * -sprite.inv_mass

            self.angular_velocity += math.degrees(
                self.inv_moment_of_inertia * (arm1 ** impulse_vector)
            )
            sprite.angular_velocity -= math.degrees(
                sprite.inv_moment_of_inertia * (arm2 ** impulse_vector)
            )

        try:
            distance = self.position - sprite.position
            pen = collision.penetration
            if (not distance) or not (self.inv_mass + sprite.inv_mass):
                return
            pen_res = distance.normalized() * pen / (self.inv_mass + sprite.inv_mass)

            # percent = 0.4
            # slop = 0.05
            # pen_res = max(pen - slop, 0.0) / (self.inv_mass + sprite.inv_mass) * percent * distance.normalized()

            self.position += pen_res * self.inv_mass
            sprite.position += - pen_res * sprite.inv_mass

        except StopIteration:
            pass

    def friction(self, _sprite, collision, j):
        t = _sprite.velocity - (_sprite.velocity * collision.tangent) * collision.tangent
        if t:
            t.normalize()

        jt = - (_sprite.velocity * t)
        jt *= _sprite.mass

        mu = math.hypot(self.static_friction, _sprite.static_friction)
        if abs(jt) < j * mu:
            frictionImpulse = - jt * t
        else:
            dynamic_friction = math.hypot(self.dynamic_friction, _sprite.dynamic_friction)
            frictionImpulse = -jt * t * dynamic_friction

        _sprite.velocity -= (1 / _sprite.mass) * frictionImpulse
        self.velocity += (1 / self.mass) * frictionImpulse
        _sprite.update_velocity_and_acceleration(base_sprites.BaseSprite.game_states['dtime'])


class c2(RigidCube):
    def __init__(self, *args, **kwargs):
        super(c2, self).__init__(*args, **kwargs, density=999999999)
        self.static_friction = 0
        self.dynamic_friction = 0

    def apply_gravity(self):
        return


class c3(RigidCube):
    def __init__(self, *args, **kwargs):
        super(c3, self).__init__(*args, **kwargs, density=1)
        self.control = base_control.AllDirectionMovement(self)

    def apply_gravity(self):
        return

    def collision(self, other):
        return True


def main():
    W = 1000
    H = 700
    screen = pygame_structures.DisplayMods.Windowed((W, H))
    pygame_structures.Camera.init(screen, "static", None)

    # from sprites import Tank
    # tank1 = Tank(structures.Direction.right, (600, 550), shoot_key=pg.K_KP_ENTER,
    #              health_bar_color=(pg.Color('green'), pg.Color('red')))

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
    fps = 60
    elapsed = 1 / fps
    running = True
    cube = None
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
                    print("here")
                    if cube is not None:
                        pygame_structures.Camera.set_scroller_position(cube, True)

                elif event.button in (5, 4):
                    if cube is None:
                        cube = c3(50, *event.pos)
                        # pygame_structures.Camera.set_scroller_position(cube, True)
                    elif event.button == 5:
                        cube.rotate(3)
                    elif event.button == 4:
                        cube.rotate(-3)
                else:
                    cube = c2(50, *event.pos)

        keys = pg.key.get_pressed()
        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    main()

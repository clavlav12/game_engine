from Engine import pygame_structures
from Engine import base_sprites
from Engine import base_control
from Engine import structures
from Engine import Geometry
from typing import Union, Tuple, List
from collections import namedtuple
import pygame as pg
import math
import os

Vector2 = structures.Vector2
manifold = namedtuple('Manifold', ('min', 'max', 'collision_vertex'))


class RotationMatrix:
    def __init__(self, angle):
        self.tl = structures.DegTrigo.cos(angle)
        self.tr = -structures.DegTrigo.sin(angle)
        self.bl = -self.tr
        self.br = self.tl

    def __mul__(self, other):
        if isinstance(other, structures.Vector2):
            return structures.Vector2.Cartesian(
                self.tl * other.x + self.tr * other.y,
                self.bl * other.x + self.br * other.y
            )
        return NotImplemented

    def __rmul__(self, other):
        return self * other


class Ball:
    def __init__(self, r, center):
        self.center = structures.Vector2.Point(center)
        self.r = r

    def is_colliding(self, other):
        return math.hypot(*(self.center - other.center)) < self.r + other.r

    def draw(self):
        draw_circle(self.center, self.r, 2)


class RigidBall(base_sprites.ImagedRigidBody):
    def __init__(self, radius, x, y, control=False, *, color=pg.Color('red')):
        """
        :param radius:
        :param x: center x position
        :param y: center y position
        """
        image = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
        pg.draw.circle(image, color, (radius, radius), radius)
        rect = pg.Rect(x - radius, y - radius, radius * 2, radius * 2)
        density = 1
        mass = radius ** 2 * math.pi * density
        if control:
            mass = 500000

        if not control:
            super(RigidBall, self).__init__(image, rect, mass, math.pi * radius ** 4 / 4, 0)
        else:
            super(RigidBall, self).__init__(image, rect, mass, math.pi * radius ** 4 / 4, 0,
                                            control=base_control.AllDirectionMovement(self))

        self.generate_collision_manifold = False
        self.collision_manifold_generator = self.ball2ball
        self.radius = radius
        self.vertices = [None, None]

        self.restitution = .2

        self.normals_length = 1

    def apply_gravity(self):
        pass

    def collision(self, other, collision):
        if not isinstance(other, RigidBall):
            return False

        OBB.collision_detection(self, other)
        # self.resolve_collision(other, collision)
        return True

    def get_axes(self, other):
        if isinstance(other, RigidBall):
            return [(other.position - self.position).normalized()]
        return [(closest_vertex_to_point(other.vertices, self.position) - self.position).normalized()]

    def resolve_collision(self, other, manifold):
        is_collision = self.resolve_penetration(other, manifold)
        if not is_collision:
            return
        normal = (self.position - other.position).normalized()
        relative_velocity = self.velocity - other.velocity
        separating_velocity = relative_velocity * normal

        new_separating_velocity = - separating_velocity * min(self.elasticity, other.elasticity)

        vel_sep_diff = new_separating_velocity - separating_velocity
        impulse = vel_sep_diff / (self.inv_mass + other.inv_mass)
        impulse_vector = normal * impulse

        self.velocity += impulse_vector * self.inv_mass
        other.velocity += impulse_vector * -other.inv_mass

    def resolve_penetration(self, other, manifold):
        distance = self.position - other.position
        pen = self.radius + other.radius - abs(distance)
        if pen < 0:
            return False
        pen_res = distance.normalized() * pen / (self.inv_mass + other.inv_mass)

        self.position += pen_res * self.inv_mass
        other.position += -pen_res * other.inv_mass
        return True

    def update(self, control_dict):
        friction = 0
        self.velocity.x -= min(friction * control_dict['dtime'] * structures.sign(self.velocity.x),
                               self.velocity.x, key=abs)
        self.velocity.y -= min(friction * control_dict['dtime'] * structures.sign(self.velocity.y),
                               self.velocity.y, key=abs)

    def ball2ball(self, other: Union[base_sprites.Tile,
                                     base_sprites.BaseSprite,
                                     pg.sprite.Sprite]):
        pass

    def update_vertices(self, axis):
        self.vertices[0] = self.position + axis * -self.radius
        self.vertices[1] = self.position + axis * self.radius


class WallControl(base_control.BaseControl):
    def __init__(self, sprite: base_sprites.BaseRigidBody):
        super(WallControl, self).__init__(sprite, structures.Direction.right)

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        keys = kwargs['keys']
        if keys[pg.K_RIGHT]:
            # self.sprite.start += structures.Vector2.Cartesian(-1, 0)
            self.sprite.angular_velocity = 150
            self.sprite.update_attributes()
        if keys[pg.K_LEFT]:
            # self.sprite.start += structures.Vector2.Cartesian(1, 0)
            self.sprite.angular_velocity = - 150
            self.sprite.update_attributes()


class RigidControl(base_control.AllDirectionSpeed):
    def __init__(self, sprite: base_sprites.BaseRigidBody, key_up, key_down, key_left, key_right,
                 roll_cw, roll_ccw):
        super(RigidControl, self).__init__(sprite, key_up, key_down, key_right, key_left)
        self.set_controls(key_up, key_down, key_left, key_right, roll_cw, roll_ccw)

    def set_controls(self, key_up, key_down, key_left, key_right, key_cw=None, key_ccw=None):
        self.controls = base_control.controls(*(base_control.Key(x) for x in
                                                (key_up, key_down, key_left, key_right, key_cw, key_ccw)))

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        super(RigidControl, self).move(**kwargs)
        keys = kwargs['keys']
        new_press = self.controls.cw.set_pressed_auto(keys)
        if new_press:  # moving right
            self.sprite.angular_velocity = 150
        new_press = self.controls.ccw.set_pressed_auto(keys)
        if new_press:  # moving right
            self.sprite.angular_velocity = - 150


class RigidConvexPolygon(base_sprites.BaseRigidBody):
    def __init__(self,
                 density,
                 vertices: List[Union[Vector2, Tuple, List]],
                 controls=base_control.NoMoveControl()):

        self.color = pg.Color('white')
        self.polygon = Geometry.Polygon(vertices, density)

        super(RigidConvexPolygon, self).__init__(
            self.polygon.rect,
            self.polygon.mass,
            self.polygon.moment_of_inertia,
            0,
            controls
        )

        self.position = self.polygon.centroid.copy()
        self.normals_length = len(self.vertices)

    @property
    def vertices(self):
        return self.polygon.world_vertices

    def collision(self, other, collision):
        # if not isinstance(other, RigidConvexPolygon):
        #     return False

        detection = self.collision_detection(self, other)
        if not detection:
            try:
                pygame_structures.Camera.remove_text('collision')
            except AttributeError:
                pass

            return False
        pygame_structures.Camera.display_text('collision!', (50, 50), 'collision')

        return True

    def get_axes(self, _):
        return [v.normalize().normal() for v in self.vertices]

    @classmethod
    def collision_detection(cls, self, other):
        """
        Implemented using the separating axis theorem
        :param self:  RigidConvexPolygon / Circle
        :param other: another RigidConvexPolygon / Circle
        :return: ...
        """
        min_overlap = float('inf')
        smallest_axis = None

        axes = find_axes(self, other)
        first_shape_axes = self.normals_length

        for i, axis in enumerate(axes):
            proj1 = cls.projection_onto_axis(self, axis)

            proj2 = cls.projection_onto_axis(other, axis)
            
            # draw_circle(other.vertices[0], 10, 2)
            # draw_circle(other.vertices[1], 10, 2)
            overlap = min(proj1.max, proj2.max) - max(proj1.min, proj2.min)
            if overlap < 0:
                return False

            if (proj1.max > proj2.max and proj1.min < proj2.min) or \
                    (proj1.max < proj2.max and proj1.min > proj2.min):
                mins = abs(proj1.min - proj2.min)
                maxs = abs(proj1.max - proj2.max)
                if mins < maxs:
                    overlap += mins
                else:
                    overlap += maxs
                    axis = axis * -1

            if overlap < min_overlap:
                min_overlap = overlap
                smallest_axis = axis
                if i < first_shape_axes:
                    vertex_object = other
                    if proj1.max > proj2.max:
                        smallest_axis *= -1
                else:
                    vertex_object = self
                    if proj1.max < proj2.max:
                        smallest_axis *= -1

        contact_vertex = cls.projection_onto_axis(vertex_object, smallest_axis).collision_vertex
        draw_arrow(contact_vertex, smallest_axis, scale=min_overlap)
        return True

    @staticmethod
    def projection_onto_axis(obj, axis: Vector2):
        if isinstance(obj, RigidBall):
            obj.update_vertices(axis)
        min_projection = float('inf')
        max_projection = float('-inf')

        collision_vertex = obj.vertices[0]
        for vertex in obj.vertices:
            projection = axis * vertex

            if projection < min_projection:
                min_projection = projection
                collision_vertex = vertex.copy()

            if projection > max_projection:
                max_projection = projection

        return manifold(min_projection, max_projection, collision_vertex)

    def update_position(self, time_delta):
        super(RigidConvexPolygon, self).update_position(time_delta)
        # self.polygon.update_centroid(self.position)
        self.polygon.rotate(self.orientation, self.position)
        self.rect = self.polygon.rect

    def draw(self):
        self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
        pg.draw.polygon(self.image, self.color, [tuple(v - self.rect.topleft) for v in self.polygon.world_vertices], 3
                        )
        # self.draw_rect()
        super(RigidConvexPolygon, self).draw()


def find_axes(o1, o2):
    return [*o1.get_axes(o2), *o2.get_axes(o1)]


def closest_vertex_to_point(vertices, p):
    closest_vertex = None
    min_distance = float('inf')

    for vertex in vertices:
        distance = (p - vertex).square_magnitude()
        if distance < min_distance:
            closest_vertex = vertex.copy()
            min_distance = distance

    return closest_vertex


class OBB(RigidConvexPolygon):
    def __init__(self, p1, p2, width, controls: base_control.controls=None):

        vertex = [
            structures.Vector2.Point(p1),
            structures.Vector2.Point(p2),
            None,
            None
        ]

        self.edge = vertex[1] - vertex[0]
        self.length = self.edge.magnitude()
        self.dir = self.edge.normalized()
        self.ref_dir = self.edge.normalized()
        self.width = width
        vertex[2] = vertex[1] + self.dir.perpendicular() * self.width
        vertex[3] = vertex[2] - self.dir * self.length

        control = base_control.NoMoveControl()
        if controls is not None:
            control = RigidControl(self, *controls)

        super(OBB, self).__init__(1, vertex, control)

        self.normals_length = 2

    def update_position(self, time_delta):
        super(OBB, self).update_position(time_delta)

    def update(self, control_dict):
        # self.apply_gravity()
        friction = 1000
        # self.angular_velocity -= min( friction/ 2 * control_dict['dtime'] * structures.sign(self.angular_velocity),
        #                              self.angular_velocity, key=abs)
        self.angular_velocity -= min(friction *
                                     control_dict['dtime'] * structures.sign(self.angular_velocity),
                                     self.angular_velocity, key=abs)

        self.velocity.r -= min(friction * control_dict['dtime'] * structures.sign(self.velocity.r),
                               self.velocity.r, key=abs)

    def get_axes(self, _):
        direction = (self.vertices[1] - self.vertices[0]).normalized()
        return [direction, direction.normal()]


class Capsule(base_sprites.BaseRigidBody):
    def __init__(self, p1, p2, radius, controls=None, density=1):
        self.p1 = structures.Vector2.Point(p1)
        self.p2 = structures.Vector2.Point(p2)

        self.r = radius

        self.color = pg.Color('white')
        self.width = 2

        self.ref_dir = (self.p2 - self.p1).normalized()
        self.ref_angle = math.acos(self.ref_dir * structures.Vector2.Cartesian(1, 0))
        self.dir = self.ref_dir.copy()
        if self.ref_dir ** structures.Vector2.Cartesian(1, 0) > 0:
            self.ref_angle *= -1
        self.length = (self.p1 - self.p2).magnitude()
        rect = self.get_rect()
        if controls is not None:
            control = RigidControl(self, *controls)

        else:
            control = base_control.NoMoveControl()

        mass = density * ((radius ** 2 * math.pi) + (self.r * 2 * self.length))
        # mass = h
        super(Capsule, self).__init__(rect,
                                      mass,
                                      mass * (self.r ** 2 * 4 + (self.length + 2*self.r)**2) / 12,
                                      0,
                                      control
                                      )

        self.elasticity = .4
        self.redraw_image()

        self.p1_offset = self.p1 - self.position
        self.p2_offset = self.p2 - self.position

    def redraw_image(self):
        image = pg.Surface(structures.add_tuples(self.get_rect().size, (self.width, self.width)), pg.SRCALPHA)
        angle = math.radians(self.orientation)

        a1 = self.ref_angle + angle + math.pi / 2
        a2 = self.ref_angle + angle + 3 * math.pi / 2

        a1 *= -1
        a2 *= -1
        modulo_360 = lambda x: x % (math.pi * 2)

        left = min(self.p1, self.p2, key=lambda v: v.x)
        right = max(self.p1, self.p2, key=lambda v: v.x)
        pg.draw.arc(image, self.color, self.rect_of_circle(left - self.rect.topleft, self.r),
                    min(a1, a2, key=modulo_360),
                    max(a1, a2, key=modulo_360),
                    self.width
                    )

        pg.draw.arc(image, self.color, self.rect_of_circle(right - self.rect.topleft, self.r),
                    max(a1, a2, key=modulo_360),
                    min(a1, a2, key=modulo_360),
                    self.width
                    )

        v = self.dir.normal()
        pg.draw.line(image, self.color,
                     tuple(self.p1 - self.rect.topleft + v * self.r),
                     tuple(self.p2 - self.rect.topleft + v * self.r),
                     self.width
                     )
        pg.draw.line(image, self.color,
                     tuple(self.p1 - self.rect.topleft - v * self.r),
                     tuple(self.p2 - self.rect.topleft - v * self.r),
                     self.width
                     )

        self.image = image

    def update_position(self, time_delta):
        super(Capsule, self).update_position(time_delta)
        rot_mat = RotationMatrix(self.orientation)
        self.dir = rot_mat * self.ref_dir

        com = self.position
        self.p1 = com + (self.dir * (-self.length / 2))
        self.p2 = com + (self.dir * (self.length / 2))
        c = self.rect.center
        self.rect = self.get_rect()
        self.rect.center = c

    def draw(self):
        draw_circle(self.p1)
        draw_circle(self.p2)
        draw_circle(self.position)
        self.redraw_image()
        super(Capsule, self).draw()

    def segment_length(self):
        return (self.p1 - self.p2).magnitude()

    def get_rect(self):
        left = min(self.p1.x, self.p2.x) - self.r
        top = min(self.p1.y, self.p2.y) - self.r
        width = abs(self.p1.x - self.p2.x) + self.r * 2
        height = abs(self.p1.y - self.p2.y) + self.r * 2
        return pg.Rect(left, top, width, height)

    @staticmethod
    def rect_of_circle(center, radius):
        r = pg.Rect(0, 0, radius * 2, radius * 2)
        r.center = tuple(center)
        return r

    def update(self, control_dict):
        self.apply_gravity()
        friction = 0
        self.angular_velocity -= min(friction * control_dict['dtime'] * structures.sign(self.angular_velocity),
                                     self.angular_velocity, key=abs)

        self.velocity.r -= min(friction * control_dict['dtime'] * structures.sign(self.velocity.r),
                               self.velocity.r, key=abs)

    def shortest_line(self, point):
        ball_to_start = self.p1 - point
        if self.dir * ball_to_start > 0:
            return self.p1

        ball_to_end = point - self.p2
        if self.dir * ball_to_end > 0:
            return self.p2

        closest_distance = self.dir * ball_to_start
        closest_vector = self.dir * closest_distance
        return self.p1 - closest_vector

    def shortest_point(self, other):
        shortest_distance = (other.shortest_line(self.p1) - self.p1).magnitude()
        closest_points = [self.p1, other.shortest_line(self.p1)]
        if (other.shortest_line(self.p2) - self.p2).magnitude() < shortest_distance:
            shortest_distance = (other.shortest_line(self.p2) - self.p2).magnitude()
            closest_points = [self.p2, other.shortest_line(self.p2)]

        if (self.shortest_line(other.p1) - other.p1).magnitude() < shortest_distance:
            shortest_distance = (self.shortest_line(other.p1) - other.p1).magnitude()
            closest_points = [self.shortest_line(other.p1), other.p1]

        if (self.shortest_line(other.p2) - other.p2).magnitude() < shortest_distance:
            shortest_distance = (self.shortest_line(other.p2) - other.p2).magnitude()
            closest_points = [self.shortest_line(other.p2), other.p2]

        # pg.draw.line(pygame_structures.Camera.screen, pg.Color('red'), tuple(closest_points[0]),
        #              tuple(closest_points[1]))
        b1 = Ball(self.r, closest_points[0])
        b2 = Ball(other.r, closest_points[1])
        # b1.draw()
        # b2.draw()
        # print(b1.is_colliding(b2))

        return closest_points

    def collision_detection(self, other):
        closest_points = self.shortest_point(other)
        b1 = Ball(self.r, closest_points[0])
        b2 = Ball(other.r, closest_points[1])
        yield b1.is_colliding(b2)
        yield b1, b2

    def penetration_resolution(self, other, b1, b2):
        distance = b1.center - b2.center
        pen = b1.r + b2.r - abs(distance)
        if pen < 0:
            return False

        if (not distance) or not (self.inv_mass + other.inv_mass):
            return

        pen_res = distance.normalized() * pen / (self.inv_mass + other.inv_mass)

        # percent = 0.4
        # slop = 0.05
        # pen_res = max(pen - slop, 0.0) / (self.inv_mass + other.inv_mass) * percent * distance.normalized()

        self.position += pen_res * self.inv_mass
        other.position += - pen_res * other.inv_mass
        # self.p1 += pen_res * self.inv_mass
        # self.p2 += pen_res * self.inv_mass
        #
        # other.p1 += - pen_res * other.inv_mass
        # other.p2 += - pen_res * other.inv_mass

        return True

    def collision_response(self, other, b1, b2):
        normal = (b1.center - b2.center).normalized()

        # closing velocities
        arm1 = b1.center - self.position + normal * self.r
        rot_vel1 = math.radians(self.angular_velocity) ** arm1
        close_vel1 = self.velocity + rot_vel1
        arm2 = b2.center - other.position - normal * other.r

        draw_arrow(self.position, normal, scale=50)
        draw_arrow(other.position, -normal, scale=50)
        rot_vel2 = math.radians(other.angular_velocity) ** arm2
        close_vel2 = other.velocity + rot_vel2

        # impulse augmentation
        imp_aug1 = arm1 ** normal
        imp_aug1 = imp_aug1 * self.inv_moment_of_inertia * imp_aug1
        imp_aug2 = arm2 ** normal
        imp_aug2 = imp_aug2 * other.inv_moment_of_inertia * imp_aug2

        relative_velocity = close_vel1 - close_vel2
        separating_velocity = relative_velocity * normal

        if separating_velocity > 0:
            return
        new_separating_velocity = - separating_velocity * min(self.elasticity, other.elasticity)

        vel_sep_diff = new_separating_velocity - separating_velocity

        if not (self.inv_mass + other.inv_mass + imp_aug1 + imp_aug2):
            return
        impulse = vel_sep_diff / (self.inv_mass + other.inv_mass + imp_aug1 + imp_aug2)
        impulse_vector = normal * impulse

        self.velocity += impulse_vector * self.inv_mass
        other.velocity += impulse_vector * -other.inv_mass

        self.angular_velocity += math.degrees(
            self.inv_moment_of_inertia * (arm1 ** impulse_vector)
        )
        other.angular_velocity -= math.degrees(
            other.inv_moment_of_inertia * (arm2 ** impulse_vector)
        )

        dynamic_friction = .5
        # dynamic_friction = 10
        tang = normal.tangent()
        vel_among_tang = relative_velocity * tang
        friction_impulse = dynamic_friction * vel_among_tang / (self.inv_mass + other.inv_mass + imp_aug1 + imp_aug2)
        impulse_vector = -tang * friction_impulse * base_sprites.BaseSprite.game_states['dtime'] * 10

        self.velocity += impulse_vector * self.inv_mass
        other.velocity += impulse_vector * -other.inv_mass

        self.angular_velocity += math.degrees(
            self.inv_moment_of_inertia * (arm1 ** impulse_vector)
        )
        other.angular_velocity -= math.degrees(
            other.inv_moment_of_inertia * (arm2 ** impulse_vector)
        )

    def collision(self, other, collision):
        if not isinstance(other, Capsule):
            return False

        detection = self.collision_detection(other)
        if not next(detection):
            try:
                pygame_structures.Camera.remove_text('collision')
            except AttributeError:
                pass

            return False

        b1: Ball
        b2: Ball
        b1, b2 = next(detection)

        pygame_structures.Camera.display_text('collision!', (50, 50), 'collision')

        self.penetration_resolution(other, b1, b2)
        self.collision_response(other, b1, b2)

        return True


class Wall(base_sprites.BaseRigidBody):
    def __init__(self, start: Union[structures.Vector2, tuple, list], end: Union[structures.Vector2, tuple, list]):
        self.start = structures.Vector2.Point(start)
        self.end = structures.Vector2.Point(end)

        self.ref_start = self.start.copy()
        self.ref_end = self.end.copy()
        self.ref_unit = (self.end - self.start).normalized()
        self.ref_center = (self.start + self.end) / 2

        self.orientation = 0
        # super(Wall, self).__init__(self.get_rect(), base_control.NoMoveControl(), 500)
        # super(Wall, self).__init__(self.get_rect(), WallControl(self), 500)
        super(Wall, self).__init__(self.get_rect(), 500, 1, 0, base_control.NoMoveControl())

        self.update_attributes()

        self.collide_check_by_rect = True

    def update(self, control_dict):
        rot_mat = RotationMatrix(self.orientation)
        new_dir = rot_mat * self.ref_unit

        self.start = self.ref_center + (new_dir * (-self.length / 2))
        self.end = self.ref_center + (new_dir * (self.length / 2))

        self.angular_velocity -= min(200 * control_dict['dtime'] * structures.sign(self.angular_velocity),
                                     self.angular_velocity, key=lambda x: abs(x))
        # self.angular_velocity *= 0.01 ** control_dict['dtime']

        self.update_attributes()

    @property
    def length(self):
        return (self.end - self.start).magnitude()

    def update_attributes(self):
        self.rect = self.get_rect()
        self.set_position(*self.rect.topleft)
        self.position += self.rect.size

        image = pg.Surface(self.rect.size, pg.SRCALPHA)

        pg.draw.line(
            image,
            pg.Color("black"),
            tuple(self.start - self.rect.topleft),
            tuple(self.end - self.rect.topleft),
            3
        )

        self.image = image.convert_alpha()
        self.mask = pg.mask.from_surface(self.image)

    def get_rect(self):
        left = min(self.start.x, self.end.x)
        top = min(self.start.y, self.end.y)
        width = max(abs(self.start.x - self.end.x), 1)
        height = max(abs(self.start.y - self.end.y), 1)
        return pg.Rect(left, top, width, height)

    def unit(self):
        return (self.end - self.start).normalized()

    def closest_point(self, sprite: base_sprites.BaseSprite):
        ball_to_start = self.start - sprite.position
        if self.unit() * ball_to_start > 0:
            return self.start

        ball_to_end = sprite.position - self.end
        if self.unit() * ball_to_end > 0:
            return self.end

        closest_distance = self.unit() * ball_to_start
        closest_vector = self.unit() * closest_distance
        return self.start - closest_vector

    def collision(self, other, collision):
        if not isinstance(other, RigidBall):
            return False
        if not self.collide_with(other):
            return False

        pen_vec = other.position - self.closest_point(other)
        other.position += pen_vec.normalized() * (other.radius - pen_vec.magnitude())

        normal = (other.position - self.closest_point(other)).normalized()
        separating_velocity = other.velocity * normal
        new_separating_velocity = - separating_velocity * other.elasticity
        vel_sep_diff = separating_velocity - new_separating_velocity

        other.velocity += normal * -vel_sep_diff

    def collide_with(self, other: RigidBall):
        ball_to_closest = self.closest_point(other) - other.position
        return ball_to_closest.magnitude() <= other.radius

    # def draw(self, draw_health=False):
    #     self.draw_rect()
    #     super(Wall, self).draw()


class floor(Capsule):
    def __init__(self, p1, p2):
        super(floor, self).__init__(p1, p2, 10)
        self.mass = 999999999999999999999999999999999
        self.moment_of_inertia = 999999999999999999999999999999999

    @property
    def inv_mass(self):
        return 0

    @property
    def inv_moment_of_inertia(self):
        return 0

    def update(self, _):
        pass


def draw_circle(p, r=2, w=0, color=pg.Color('red')):
    if isinstance(color, str):
        color = pg.Color(color)
    pg.draw.circle(pygame_structures.Camera.screen, color, tuple(p), r, w)


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

def Main():
    W = 1000
    H = 700

    screen = pygame_structures.DisplayMods.Windowed((W, H))
    W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

    pygame_structures.Camera.init(screen, "dynamic", None)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame_structures.Map([], [], [], [], 50)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    from random import randrange

    # RigidBall(20, randrange(0, W), randrange(0, H), True, color=pg.Color('dark green'))
    # for i in range(200):
    #     RigidBall(randrange(10, 40), randrange(0, W), randrange(0, H), False)
    # Wall((0, 0), (W, 0))
    # Wall((0, 0), (0, H))
    # Wall((0, H), (W, H))
    # Wall((W, 0), (W, H))
    # Wall((200, 200), (600, 400))

    p5, p6 = (150, 50), (151, 300)
    p7, p8 = [300, 200], [400, 300]

    p1, p2 = [296.17624, 203.80806], [395.21399, 304.76114]
    p3, p4 = [588.96370, 190.26225], [686.61919, 292.55304]

    p1, p2, v1, a1 = [353.41526, 532.55373], [240.04085, 448.01827], [348.20000, -320.20000], 0.0
    p3, p4, v2, a2 = [371.86566, 383.41364], [501.65894, 327.25579], [0.00000, 0.00000], 0.0


    p1, p2 = (150, 150), (300, 150)

    # c1 = Capsule(p1, p2, 40,
    #              base_control.controls(pg.K_w, pg.K_s, pg.K_a, pg.K_d, pg.K_e, pg.K_q)
    #              )
    #
    # c1.velocity.values = v1
    # c1.velocity /= 3
    # c1.angular_velocity = 40

    # c2 = Capsule(p3, p4, 40,
    #              base_control.controls(pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_KP0, pg.K_RCTRL)
    #              )

    # OBB((300, 180), (250, 50), 80,
    #     base_control.controls(pg.K_w, pg.K_s, pg.K_a, pg.K_d, pg.K_e, pg.K_q))
    # OBB((200, 200), (400, 300), 100,
    #     base_control.controls(pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT, pg.K_KP0, pg.K_RCTRL))
    RigidBall(50, randrange(0, W), randrange(0, H), True, color=pg.Color('dark green'))
    RigidBall(50, randrange(0, W), randrange(0, H), False, color=pg.Color('dark green'))
    # floor((0, H), (W, H))
    # floor((0, 0), (0, H))
    # floor((0, 0), (W, 0))
    # floor((W, 0), (W, H))
    # floor((0, H-200), (W, H))
    # c2.velocity.values = v2
    # c2.angular_velocity = a2

    # c2 = Capsule(p5, p6, 10, density=5)
    # c2 = Capsule(p7, p8, 10, density=5)

    # rand_point = lambda: ((randrange(50, W-50), randrange(50, H-50)), (randrange(100, 600), randrange(100, 400)))
    # c2 = Capsule(*rand_point(), randrange(10, 20), density=5)
    # c2 = Capsule(*rand_point(), randrange(10, 20), density=5)

    while running:
        events = pg.event.get()
        for event in events:
            if event.type == pg.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pg.QUIT:
                running = 0
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_y:
                    base_sprites.GRAVITY *= -1
            elif event.type == pg.MOUSEBUTTONDOWN:
                pass
                # if event.button == 1:
                #     random_planet(*add_positions(add_positions(pygame.mouse.get_pos(),
                #                                                pygame_structures.Camera.scroller.position()),
                #                                  (-W // 2, -H // 2)))
                # elif event.button == 3:
                #     pygame_structures.Camera.set_scroller_position(next_sprite(), smooth_move=True)

        keys = pg.key.get_pressed()
        if keys[pg.K_LCTRL] and keys[pg.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()
        base_sprites.tick(elapsed, keys)

        # print("c1: ", c1.p1, c1.p2, c1.velocity, c1.angular_velocity, sep=', ')
        # print("c2: ", c2.p1, c2.p2, c2.velocity, c2.angular_velocity, sep=', ')
        # c1.shortest_point(c2)
        # vec = wall.closest_point(ball) - ball.com_position
        # pg.draw.line(pygame_structures.Camera.screen,
        #              pg.Color('red'),
        #              tuple(ball.com_position),
        #              tuple(ball.com_position + vec),
        #              2)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 1 / 15)
        # elapsed = 1/800


if __name__ == '__main__':
    Main()
    # mat = RotationMatrix(30)
    # vec = structures.Vector2.Cartesian(20, 65)
    #
    # vec2 = vec.copy()
    # vec2.theta += 30

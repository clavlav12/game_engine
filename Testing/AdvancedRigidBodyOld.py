from Engine import Bodies
from Engine.Debug import *
from Engine import base_sprites
from Engine import base_control
from Engine import structures
from typing import Union, Tuple, List
from collections import namedtuple
import pygame as pg
import math
import os

Vector2 = structures.Vector2
Projection = namedtuple('Projection', ('min', 'max', 'collision_vertex'))
Number = Union[int, float]
Point = Union[List[Number], Tuple[Number, Number], Vector2]

class CollisionManifold:
    def __init__(self, contact_point, normal, depth, collision=True):
        self.contact_point = contact_point
        self.normal = normal
        self.depth = depth
        self.collision = collision

    @classmethod
    def NoCollision(cls):
        return cls(Vector2.Zero(), Vector2.Zero(), 0, False)

    def __bool__(self):
        return self.collision

    def penetration_resolution(self, obj1, obj2):
        obj1: RigidBody
        obj2: RigidBody

        if (not self.depth) or not (obj1.inv_mass + obj2.inv_mass):
            return

        pen_res = self.normal * self.depth / (obj1.inv_mass + obj2.inv_mass)

        # percent = 1
        # slop = 5
        # pen_res = max(self.depth - slop, 0.0) / (obj1.inv_mass + obj2.inv_mass) * percent * self.normal
        # print(max(self.depth - slop, 0.0))
        obj1.position += pen_res * obj1.inv_mass
        obj2.position += - pen_res * obj2.inv_mass

    def collision_response(self, obj1, obj2):
        obj1: RigidBody
        obj2: RigidBody

        # closing velocities
        arm1 = self.contact_point - obj1.position
        rot_vel1 = math.radians(obj1.angular_velocity) ** arm1
        close_vel1 = obj1.velocity + rot_vel1

        arm2 = self.contact_point - obj2.position
        rot_vel2 = math.radians(obj2.angular_velocity) ** arm2
        close_vel2 = obj2.velocity + rot_vel2

        # impulse augmentation
        imp_aug1 = arm1 ** self.normal
        imp_aug1 = imp_aug1 * obj1.inv_moment_of_inertia * imp_aug1
        imp_aug2 = arm2 ** self.normal
        imp_aug2 = imp_aug2 * obj2.inv_moment_of_inertia * imp_aug2

        relative_velocity = close_vel1 - close_vel2
        separating_velocity = relative_velocity * self.normal

        if separating_velocity > 0:
            return

        # new_separating_velocity = - separating_velocity * min(obj1.elasticity, obj2.elasticity)
        #
        # vel_sep_diff = new_separating_velocity - separating_velocity

        if not (obj1.inv_mass + obj2.inv_mass + imp_aug1 + imp_aug2):
            return
        impulse = - separating_velocity * (min(obj1.elasticity, obj2.elasticity) + 1) / (
                    obj1.inv_mass + obj2.inv_mass + imp_aug1 + imp_aug2)
        impulse_vector = self.normal * impulse

        obj1.velocity += impulse_vector * obj1.inv_mass
        obj2.velocity += impulse_vector * -obj2.inv_mass

        obj1.angular_velocity += math.degrees(
            obj1.inv_moment_of_inertia * (arm1 ** impulse_vector)
        )

        obj2.angular_velocity -= math.degrees(
            obj2.inv_moment_of_inertia * (arm2 ** impulse_vector)
        )

        self.original_friction(obj1, obj2, impulse)

    def original_friction(self, obj1, obj2, j):
        obj1: RigidBody
        obj2: RigidBody
        arm1 = self.contact_point - obj1.position
        rot_vel1 = math.radians(obj1.angular_velocity) ** arm1
        close_vel1 = obj1.velocity + rot_vel1

        arm2 = self.contact_point - obj2.position
        rot_vel2 = math.radians(obj2.angular_velocity) ** arm2
        close_vel2 = obj2.velocity + rot_vel2

        # impulse augmentation
        imp_aug1 = arm1 ** self.normal
        imp_aug1 = imp_aug1 * obj1.inv_moment_of_inertia * imp_aug1
        imp_aug2 = arm2 ** self.normal
        imp_aug2 = imp_aug2 * obj2.inv_moment_of_inertia * imp_aug2

        rv = obj2.velocity - obj1.velocity
        rv = close_vel1 - close_vel2

        normal = self.normal

        t = rv - (normal * (rv * normal))
        if not t.square_magnitude():
            return

        t.normalize()
        jt = -rv * t
        jt /= (obj1.inv_mass + obj2.inv_mass + imp_aug1 + imp_aug2)

        # if abs(jt) < 100_000:
        #     return

        sf = df = .2

        if abs(jt) < j * sf:
            tangentImpulse = t * jt
        else:
            tangentImpulse = t * -j * df

        obj1.velocity += tangentImpulse * obj1.inv_mass
        obj2.velocity -= tangentImpulse * obj2.inv_mass

        obj1.angular_velocity += math.degrees(
            obj1.inv_moment_of_inertia * (arm1 ** tangentImpulse)
        )

        obj2.angular_velocity -= math.degrees(
            obj2.inv_moment_of_inertia * (arm2 ** tangentImpulse)
        )


def friction(self, obj1, obj2, relative_velocity, imp_aug1, imp_aug2, arm1, arm2):
    obj1: RigidBody
    obj2: RigidBody
    dynamic_friction = 2
    # dynamic_friction = .2
    # dynamic_friction = 0
    tang = self.normal.tangent()
    vel_among_tang = relative_velocity * tang
    friction_impulse = dynamic_friction * vel_among_tang / (obj1.inv_mass + obj2.inv_mass + imp_aug1 + imp_aug2)
    impulse_vector = -tang * friction_impulse * base_sprites.BaseSprite.game_states['dtime'] * 10

    obj1.velocity += impulse_vector * obj1.inv_mass
    obj2.velocity += impulse_vector * -obj2.inv_mass

    obj1.angular_velocity += math.degrees(
        obj1.inv_moment_of_inertia * (arm1 ** impulse_vector)
    )
    obj2.angular_velocity -= math.degrees(
        obj2.inv_moment_of_inertia * (arm2 ** impulse_vector)
    )


# def new_friction(self, obj1, obj2, relative_velocity, imp_aug1, imp_aug2, arm1, arm2, impulse):
#     obj1: AdvancedRigidBody
#     obj2: AdvancedRigidBody
#     # dynamic_friction = 2
#     dynamic_friction = .2
#     # dynamic_friction = 0
#     tang = self.normal.tangent()
#     vel_among_tang = relative_velocity * tang
#     friction_impulse = dynamic_friction * impulse
#     impulse_vector = -tang * friction_impulse
#
#     pygame_structures.Camera.add_blit_order(lambda: draw_arrow(obj1.position, impulse_vector), .1)
#     pygame_structures.Camera.add_blit_order(lambda: draw_arrow(obj2.position, -impulse_vector), .1)
#
#     print(impulse_vector * obj1.inv_mass)
#
#     obj1.velocity += min(impulse_vector * obj1.inv_mass, obj1.velocity, key=lambda x: abs(x * tang))
#     obj1.velocity += min(- impulse_vector * obj2.inv_mass, obj2.velocity, key=lambda x: abs(x * tang))
#
#     obj1.angular_velocity += min(math.degrees(
#         obj1.inv_moment_of_inertia * (arm1 ** impulse_vector)
#     ), obj1.angular_velocity, key=abs)
#
#     obj2.angular_velocity -= math.degrees(
#         obj2.inv_moment_of_inertia * (arm2 ** impulse_vector)
#     )


class AdvancedRigidBody(base_sprites.BaseRigidBody):
    def __init__(self, mass, moment_of_inertia, orientation, components: List[Bodies.Body],
                 control: base_control.BaseControl = base_control.NoMoveControl()):
        self.components: List[Bodies.Body] = components
        super(RigidBody, self).__init__(self.get_rect(), mass, moment_of_inertia, orientation, control)

    def update(self, _):
        for comp in self.components:
            comp.update_position(self.position, self.orientation)
        self.update_rect()
        # self.top_down_friction(_)
        self.apply_gravity()

    def update_rect(self):
        self.rect = self.get_rect()

    def get_rect(self):
        # r = [comp.get_rect() for comp in self.components][0]
        # print(r, r.center)
        return self.rect_bounds(*(comp.get_rect() for comp in self.components))

    @staticmethod
    def rect_bounds(*rects: pg.Rect):
        min_vec = Vector2.Cartesian(float('inf'), float('inf'))
        max_vec = Vector2.Cartesian(float('-inf'), float('-inf'))

        for rect in rects:
            min_vec = min_vec.min(rect.topleft)
            max_vec = max_vec.max(rect.bottomright)

        return pg.Rect(*min_vec, *(max_vec - min_vec))

    def draw(self):
        for comp in self.components:
            comp.redraw()

    def collision(self, other):
        if not isinstance(other, RigidBody):
            other_components = [Bodies.AABB(other.rect)]
        else:
            other_components = other.components

        best_manifold = CollisionManifold.NoCollision()
        for self_comp in self.components:
            for other_comp in other_components:
                manifold = self.collision_detection(self_comp, other_comp)
                if manifold.depth > best_manifold.depth:
                    best_manifold = manifold
        # resolve collision
        remove = False
        if not hasattr(other, 'angular_velocity'):
            remove = True
            other.__setattr__('angular_velocity', 0)
            other.__setattr__('inv_moment_of_inertia', 0)

        best_manifold.penetration_resolution(self, other)
        best_manifold.collision_response(self, other)

        if remove:
            other.__delattr__('angular_velocity')
            other.__delattr__('inv_moment_of_inertia')

        return True

    def top_down_friction(self, control_dict):
        friction = 1000
        self.angular_velocity -= min(friction / 4 *
                                     control_dict['dtime'] *
                                     structures.sign(self.angular_velocity),
                                     self.angular_velocity, key=abs)

        self.velocity.r -= min(friction * control_dict['dtime'] * structures.sign(self.velocity.r),
                               self.velocity.r, key=abs)

    @staticmethod
    def projection_onto_axis(obj: Bodies.Body, axis: Vector2):
        obj.update_floating_vertices(axis)
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

        return Projection(min_projection, max_projection, collision_vertex)

    @classmethod
    def collision_detection(cls, self: Bodies.Body, other: Bodies.Body):
        """
        Implemented using the separating axis theorem
        :param self:  RigidConvexPolygon / Circle
        :param other: another RigidConvexPolygon / Circle
        :return: ...
        """
        min_overlap = float('inf')
        smallest_axis = None

        first_axes = self.get_normals(other)
        second_axes = other.get_normals(self)
        first_shape_axes = len(first_axes)

        axes = first_axes + second_axes

        for i, axis in enumerate(axes):
            proj1 = cls.projection_onto_axis(self, axis)

            proj2 = cls.projection_onto_axis(other, axis)

            # draw_circle(other.vertices[0], 10, 2)
            # draw_circle(other.vertices[1], 10, 2)
            overlap = min(proj1.max, proj2.max) - max(proj1.min, proj2.min)
            if overlap < 0:
                return CollisionManifold.NoCollision()

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

        if vertex_object is other:
            smallest_axis = smallest_axis * -1

        # pygame_structures.Camera.add_blit_order(lambda: draw_circle(contact_vertex, 10, 2), .03)

        return CollisionManifold(contact_vertex, smallest_axis, min_overlap)


class OBB(RigidBody):
    __key = object()

    def __init__(self, key, body, density, control: base_control.controls = None):
        if key is not self.__key:
            raise structures.PrivateConstructorAccess(f"Access denied to private"
                                                      f" constructor of class {self.__class__}")
        if control is not None:
            control = RigidControl(self, *control)
        else:
            control = base_control.NoMoveControl()

        super(OBB, self).__init__(body.polygon.area * density, body.polygon.moment_of_inertia,
                                  0, [body], control)
        self.elasticity = .2
        # self.elasticity = .0

    @classmethod
    def AxisAligned(cls, center, width_extent, height_extent, density=1, control: base_control.controls = None):
        body = Bodies.Rectangle.AxisAligned(Vector2.Point(center), width_extent, height_extent, (0, 0), 0)
        return cls(cls.__key, body, density, control)

    @classmethod
    def Oriented(cls,
                 p1: Point,
                 p2: Point,
                 width: Number,
                 density: Number = 1,
                 center_offset: Point = Vector2.Zero(),
                 orientation: Number = 0,
                 control: base_control.controls = None
                 ):
        body = Bodies.Rectangle.Oriented(p1, p2, width, center_offset, orientation)
        return cls(cls.__key, body, density, control)


class Capsule(RigidBody):
    def __init__(self, p1, p2, radius, control: base_control.controls = None, density=1):
        if control is not None:
            control = RigidControl(self, *control)

        self.p1 = structures.Vector2.Point(p1)
        self.p2 = structures.Vector2.Point(p2)
        center = (self.p1 + self.p2) / 2
        circle1 = Bodies.Circle(self.p1, radius, center - self.p1, 0)
        circle2 = Bodies.Circle(self.p2, radius, center - self.p2, 0)
        rectangle = Bodies.Rectangle.Oriented(
            self.p2 + (self.p2 - self.p1).normalized().normal() * radius,
            self.p1 + (self.p2 - self.p1).normalized().normal() * radius,
            radius * 2,
            (0, 0),
            0
        )

        length = (self.p1 - self.p2).magnitude()
        mass = density * ((radius ** 2 * math.pi) + (radius * 2 * length))

        super(Capsule, self).__init__(
            mass,
            mass * (radius ** 2 * 4 + (length + 2 * radius) ** 2) / 12,
            0,
            [circle1, circle2, rectangle],
            control
        )

        self.elasticity = .2

    def update(self, _):
        super(Capsule, self).update()
        self.apply_gravity()

    def draw(self):
        super(Capsule, self).draw()


class Wall(RigidBody):
    def __init__(self,
                 p1: Point,
                 p2: Point):
        body = Bodies.Line(p1, p2, (0, 0), 0)
        super(Wall, self).__init__(
            float('inf'),
            float('inf'),
            0,
            [body]
        )

    def collision(self, other):
        if isinstance(other, Wall):
            return True
        else:
            return super(Wall, self).collision(other)

    def draw(self):
        super(Wall, self).draw()

    def apply_gravity(self):
        pass


class Star(RigidBody):
    def __init__(self, radius, center, density=1, control: base_control.controls = None):
        if control is not None:
            # control = RigidControl(self, *control)
            control = base_control.AllDirectionMovement(self)
        else:
            control = base_control.NoMoveControl()
        tri1 = Bodies.RegularPolygon(center, radius, 3, (0, 0), 0)
        tri2 = Bodies.RegularPolygon(center, radius, 3, (0, 0), 180)
        super(Star, self).__init__(
            (tri1.polygon.area + tri2.polygon.area) * density,
            (tri1.polygon.moment_of_inertia + tri2.polygon.moment_of_inertia) * density,
            0,
            [tri1, tri2],
            control
        )

        self.elasticity = .2

    def update(self, _):
        super(Star, self).update()
        # self.apply_gravity()


class Hammer(RigidBody):
    def __init__(self, w1, h1, w2, h2, center1, density=1, control: base_control.controls = None):
        if control is not None:
            control = RigidControl(self, *control)
        else:
            control = base_control.NoMoveControl()
        rect1 = Bodies.Rectangle.AxisAligned(center1, w1 / 2, h1 / 2, (0, 0), 0)
        rect2 = Bodies.Rectangle.AxisAligned(center1 - Vector2.Cartesian(y=h1 / 2 + h2 / 2), w2 / 2, h2 / 2, (
            0, (h1 + h2) / 2), 0)

        super(Hammer, self).__init__(
            (rect1.polygon.area + rect2.polygon.area) * density,
            (rect1.polygon.moment_of_inertia + rect2.polygon.moment_of_inertia) * density,
            0,
            [rect1, rect2],
            control
        )

        self.elasticity = .2

    def update(self, _):
        super(Hammer, self).update()
        # self.apply_gravity()


class Ball(RigidBody):
    def __init__(self, center, r, density=1, control: base_control.controls = None):
        if control is not None:
            control = base_control.AllDirectionMovement(self, *control[:-2])
        else:
            control = base_control.NoMoveControl()

        body = Bodies.Circle(center, r)

        mass = r ** 2 * math.pi * density
        mmoi = mass * r ** 2
        super(Ball, self).__init__(mass, mmoi, 0, [body], control)
        self.elasticity = .2
        self.r = r

    # def apply_gravity(self):
    #     pass

    def draw(self):
        super(Ball, self).draw()
        pos = tuple(self.position.floor())
        pg.draw.line(pygame_structures.Camera.screen, pg.Color('white'), pos,
                     structures.add_tuples(
                         (self.r * structures.DegTrigo.cos(self.orientation),
                          self.r * structures.DegTrigo.sin(self.orientation)
                          ),
                         pos
                     )
                     )


class Builder:
    def __init__(self):
        self.points = []

    def add_point(self, point):
        self.points.append(point)

        if len(self.points) >= 2:
            Wall(self.points[0], self.points[1])
            self.points.clear()

    def draw(self):
        if self.points:
            pg.draw.line(
                pygame_structures.Camera.screen,
                pg.Color('red'),
                self.points[0],
                pg.mouse.get_pos()
            )


def get_tile_map(W, H, ts):
    tile_list = [
        [{'id': 3} for _ in range(W//ts)] for __ in range(H//ts)
    ]

    sur = pg.Surface((ts, ts)).convert()
    sur.fill((0, 0, 255))

    collection = pygame_structures.TileCollection()
    for i in range(0, W//ts):
        tile_list[0][i] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, W//ts):
        tile_list[H//ts-1][i] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, H//ts):
        tile_list[i][W//ts-1] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, H//ts):
        tile_list[i][0] = {'id': 1, 'img': sur, 'group': collection}

    return tile_list
    # tile_list[0][0] = {'id': 6, 'group': collection}


def Main():
    import random

    class Planet(base_sprites.BaseSprite):
        # GravitationalConstant = .1e-2
        GravitationalConstant = 100
        # CoulombConstant = .1e-2
        fnt = pg.font.SysFont('comicsansms', 12)

        def __init__(self, x, y, density, color, radius):
            mass = density * math.pi * radius ** 2
            self.image = pg.Surface((radius * 2, radius * 2), 32)
            # pg.draw.circle(self.image, color, (radius, radius), radius)
            self.image.convert_alpha()
            super(Planet, self).__init__(pg.Rect(x - radius, y - radius, radius * 2, radius * 2),
                                         base_control.BaseControl(self, structures.Direction.right), mass)
            self.color = color
            self.radius = radius

            self.mass_text = self.fnt.render(f'{self.mass:,}', True, pg.Color('green'))
            self.mass_rect = self.mass_text.get_rect()

            self.elasticity = .2

        def set_mass(self, value):
            self.mass = value
            self.mass_text = self.fnt.render(f'{self.mass:,}', True, pg.Color('green'))
            self.mass_rect = self.mass_text.get_rect()

        def update(self, control_dict):
            super(Planet, self).update(control_dict)
            self.apply_gravity()

        @staticmethod
        def distance(pos1, pos2):
            return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

        @staticmethod
        def ceil(min_, max_, num):
            return min(max(num, min_), max_)

        def draw(self):
            self.rect.x -= self.radius + self.rect.width // 2
            self.rect.y -= self.radius + self.rect.height // 2
            super(Planet, self).draw()
            self.rect.x += self.radius - self.rect.width // 2
            self.rect.y += self.radius - self.rect.height // 2
            self.mass_rect.center = self.rect.center
            self.mass_rect.bottom = self.rect.top
            r = pg.Rect(self.mass_rect)
            r.topleft = r.topleft - pygame_structures.Camera.scroller
            pygame_structures.Camera.blit(self.mass_text, r)
            # self.draw_rect()

    W = 1000
    H = 700

    screen = pygame_structures.DisplayMods.Windowed((W, H))
    W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

    pygame_structures.Camera.init(screen, "static", None)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    ts = 50
    pygame_structures.Map(get_tile_map(W, H, ts), [], [], [], ts)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    # b2 = OBB.Oriented((200, 200), (400, 300), 100,
    #          control=base_control.arrows)

    p1, p2 = (150, 150), (300, 150)
    # c1 = Capsule(p1, p2, 40,
    #              base_control.wasd
    #              )

    # c1 = Hammer(20, 100, 70, 20, (500, 500), control=base_control.wasd)
    # c1 = Hammer(20, 100, 70, 20, (500, 500))
    # c1 = Hammer(20, 100, 70, 20, (500, 500))
    # c1 = Hammer(20, 100, 70, 20, (500, 500))
    # c1 = Hammer(20, 100, 70, 20, (500, 500))
    # c1 = Hammer(20, 100, 70, 20, (500, 500))
    # c1.position.values, c1.velocity.values, c1.angular_velocity, c1.orientation = \
    #     [194.46942, 592.08483], [0.00000, -1.41152], 1.3099259531023957, 115.1044798143625

    # center1 = (500, 500)
    # w1, h1 = 50, 20
    # h2, w2 = 50, 20
    # rect1 = OBB.AxisAligned((W/2, 100), 25, 25)
    # rect2 = OBB.AxisAligned(center1 - Vector2.Cartesian(y=h1 / 2 + h2 / 2), w2 / 2, h2 / 2)

    # Star(50, (500, 500), 1, base_control.wasd)
    Ball((500, 500), 50, 1, base_control.wasd)
    Wall((0, 0), (W, 0))
    Wall((0, 0), (0, H))
    Wall((W, 0), (W, H))
    Wall((0, H), (W, H))
    Wall((W / 3, H / 2), (2 * W / 3, H / 2))
    # Planet(500, 500, 1, pg.Color('red'), 50)
    builder = Builder()
    c = None
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
                if event.button == 1:
                    builder.add_point(event.pos)

                elif event.button == 3:
                    c = {
                        0: (lambda: OBB.AxisAligned(event.pos, 25, 25)),
                        1: (lambda: Ball(event.pos, 25, 1)),
                        2: (lambda: Star(25, event.pos))
                    }[random.randrange(3)]()

                    # Star(25, event.pos)
                    # Ball(event.pos, 25)

        keys = pg.key.get_pressed()
        if keys[pg.K_LCTRL] and keys[pg.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()
        base_sprites.tick(elapsed, keys)
        if c is not None:
            draw_arrow(c.position, c.velocity)
        builder.draw()
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 1 / 15)
        # elapsed = 1/800


if __name__ == '__main__':
    Main()

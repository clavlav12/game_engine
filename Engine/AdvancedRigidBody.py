from Engine import pygame_structures
from Engine.Debug import *
from Engine import base_sprites
from Engine import base_control
from Engine import structures
from Engine import Geometry
from CollisionManifold import ManifoldGenerator, CollisionManifold
from typing import Union, Tuple, List
from collections import namedtuple
import Bodies
import pygame as pg
import math
import os

Vector2 = structures.Vector2
Projection = namedtuple('Projection', ('min', 'max', 'collision_vertex'))
Number = Union[int, float]
Point = Union[List[Number], Tuple[Number, Number], Vector2]


def advanced_rigid_generator(obj1, obj2):
    if isinstance(obj1, AdvancedRigidBody):
        self = obj1
        other = obj2
    else:
        self = obj2
        other = obj1

    if not isinstance(other, AdvancedRigidBody):
        if isinstance(other, base_sprites.BaseRigidBody):
            other.obb.update_position(other.position, other.orientation)
            other_components = [other.obb]
        else:
            other_components = [Bodies.AABB(other.rect)]
    else:
        other_components = other.components

    best_manifold = CollisionManifold.NoCollision()
    for self_comp in self.components:
        for other_comp in other_components:
            manifold = self.collision_detection(self_comp, other_comp)
            if manifold.depth > best_manifold.depth:
                best_manifold = manifold

    if best_manifold.collision:
        CollisionManifold.add_manifold(best_manifold)
        best_manifold.obj1 = self
        best_manifold.obj2 = other
        return best_manifold


class AdvancedRigidBody(base_sprites.BaseRigidBody):
    advanced_rigid_generator = ManifoldGenerator(advanced_rigid_generator, 3)

    def __init__(self, mass, moment_of_inertia, orientation, components: List[Bodies.Body],
                 control: base_control.BaseControl = base_control.NoMoveControl()):
        self.components: List[Bodies.Body] = components
        super(AdvancedRigidBody, self).__init__(
            self.get_rect(),
            mass,
            moment_of_inertia,
            orientation,
            control,
            manifold_generator=self.advanced_rigid_generator
        )

    def update(self, _):
        self.set_position()
        # self.top_down_friction(_)
        self.apply_gravity()

    def set_position(self, x=None, y=None):
        for comp in self.components:
            comp.update_position(self.position, self.orientation)
        self.update_rect()

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

    def top_down_friction(self, control_dict):
        friction = 1000
        self.angular_velocity -= min(friction / 4 *
                                     control_dict['dtime'] *
                                     structures.sign(self.angular_velocity),
                                     self.angular_velocity, key=abs)

        self.velocity.r -= min(friction * control_dict['dtime'] * structures.sign(self.velocity.r),
                               self.velocity.r, key=abs)


class OBB(AdvancedRigidBody):
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


class Capsule(AdvancedRigidBody):
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
        super(Capsule, self).update(_)
        self.apply_gravity()

    def draw(self):
        super(Capsule, self).draw()


class Wall(AdvancedRigidBody):
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


class Star(AdvancedRigidBody):
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
        super(Star, self).update(_)
        # self.apply_gravity()


class Hammer(AdvancedRigidBody):
    def __init__(self, w1, h1, w2, h2, center1, density=1, control: base_control.controls = None):
        if control is not None:
            control = base_control.AllDirectionMovement(self, *control[:-2])
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
        super(Hammer, self).update(_)
        # self.apply_gravity()


class Ball(AdvancedRigidBody):
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
        # self.draw_rect()


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
        [{'id': 3} for _ in range(W // ts)] for __ in range(H // ts)
    ]

    sur = pg.Surface((ts, ts)).convert()
    sur.fill((0, 0, 255))

    collection = pygame_structures.TileCollection()
    for i in range(0, W // ts):
        tile_list[0][i] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, W // ts):
        tile_list[H // ts - 1][i] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(1, H // ts - 1):
        tile_list[i][W // ts - 1] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(1, H // ts - 1):
        tile_list[i][3] = {'id': 1, 'img': sur, 'group': collection}

    return tile_list
    # tile_list[0][0] = {'id': 6, 'group': collection}


def resolve_collisions():
    for manifold in CollisionManifold.Manifolds:
        self = manifold.obj1
        other = manifold.obj2
        # resolve collision
        remove = False
        if not hasattr(other, 'angular_velocity'):
            remove = True
            other.__setattr__('angular_velocity', 0)
            other.__setattr__('inv_moment_of_inertia', 0)

        manifold.collision_response(self, other)

        if remove:
            other.__delattr__('angular_velocity')
            other.__delattr__('inv_moment_of_inertia')

    for manifold in CollisionManifold.Manifolds:
        self = manifold.obj1
        other = manifold.obj2
        # resolve collision
        remove = False
        if not hasattr(other, 'angular_velocity'):
            remove = True
            other.__setattr__('angular_velocity', 0)
            other.__setattr__('inv_moment_of_inertia', 0)

        manifold.penetration_resolution(self, other)

        if remove:
            other.__delattr__('angular_velocity')
            other.__delattr__('inv_moment_of_inertia')

    CollisionManifold.Manifolds.clear()


def t(n=1):
    # print(len(CollisionManifold.Manifolds))
    if n > 0:
        sprites_set = set()
        for m in CollisionManifold.Manifolds:
            sprites_set.add(m.obj1)
            sprites_set.add(m.obj2)
    resolve_collisions()
    for i in range(n - 1):
        base_sprites.BaseSprite.check_sprite_collision(lst=sprites_set)
        resolve_collisions()


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
                                         base_control.BaseControl(self, structures.Direction.right), mass,
                                         manifold_generator=base_sprites.BaseSprite.basic_generator)
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
        #     self.rect.x -= self.radius + self.rect.width // 2
        #     self.rect.y -= self.radius + self.rect.height // 2
        #     super(Planet, self).draw()
        #     self.rect.x += self.radius - self.rect.width // 2
        #     self.rect.y += self.radius - self.rect.height // 2
        #     self.mass_rect.center = self.rect.center
        #     self.mass_rect.bottom = self.rect.top
        #     r = pg.Rect(self.mass_rect)
        #     r.topleft = r.topleft - pygame_structures.Camera.scroller
        #     pygame_structures.Camera.blit(self.mass_text, r)
            super(Planet, self).draw()
            # self.draw_rect()
            draw_circle(self.position)

    W = 1000
    H = 700

    screen = pygame_structures.DisplayMods.Windowed((W, H))
    W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

    pygame_structures.Camera.init(screen, "static", None)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    ts = 50
    pygame_structures.Map(get_tile_map(W, H, ts), [], [], [], ts)
    # pygame_structures.Map([], [], [], [], ts)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    # b2 = OBB.Oriented((200, 200), (400, 300), 100,
    #          control=base_control.arrows)

    p1, p2 = (150, 150), (300, 150)
    # c1 = Capsule(p1, p2, 40,
    #              base_control.wasd
    #              )

    c1 = Hammer(20, 100, 70, 20, (500, 500), control=base_control.wasd)
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
    # b = Ball((500, 500), 50, 1, base_control.wasd)
    # Wall((0, 0), (W, 0))
    # Wall((0, 0), (0, H))
    # Wall((W, 0), (W, H))
    # Wall((0, H), (W, H))
    # Wall((W / 3, H / 2), (2 * W / 3, H / 2))
    # Planet(500, 500, 1, pg.Color('red'), 50)
    # Planet(500, 600, 1, pg.Color('red'), 50)
    builder = Builder()
    # c = Ball((500, H-100), 25, 1)
    # c.angular_velocity = 900
    # sp = c.position.copy()
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
                    # base_sprites.GRAVITY = 1500
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    builder.add_point(event.pos)

                elif event.button == 3:
                    c = {
                        0: (lambda: OBB.AxisAligned(event.pos, 25, 25)),
                        1: (lambda: Ball(event.pos, 25, 1)),
                        2: (lambda: Star(25, event.pos))
                    }[random.randint(0, 2)]()

                    # Star(25, event.pos)
                    # Ball(event.pos, 25)
        # try:
        #     print(c.orientation)
        # except UnboundLocalError:
        #     pass
        keys = pg.key.get_pressed()
        if keys[pg.K_LCTRL] and keys[pg.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()
        base_sprites.tick(elapsed, keys)
        # if c is not None:
        # draw_arrow(c.position, c.velocity)
        builder.draw()

        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 1 / 60)

        # elapsed = 1/800
        # elapsed = 1/60



if __name__ == '__main__':
    Main()

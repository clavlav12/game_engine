import Engine.base_control as controls
import Engine.Particle as Particles
import Engine.structures as structures
import Engine.pygame_structures as pygame_structures
from Engine import Sound
from CollisionManifold import ManifoldGenerator, CollisionManifold
import pygame
from typing import Tuple, Optional, Union
from pymaybe import maybe
from time import time
from random import shuffle
from collections import namedtuple
from Engine.Debug import *
import math
import Bodies
import os

Projection = namedtuple('Projection', ('min', 'max', 'collision_vertex'))
player = Sound.Player()
clock = pygame.time.Clock()
GRAVITY = 3_000
GRAVITY = 1_500
# GRAVITY = 500


def no_generator(a, b):
    pass


def empty_solver(manifold):
    pass


class Collider:

    empty_generator = ManifoldGenerator(no_generator, -float('inf'))

    def __init__(self,
                 sprites_collision_by_rect: bool,
                 tile_collision_by_rect: bool,
                 manifold_generator: ManifoldGenerator = empty_generator,
                 ):
        self.manifold_generator = manifold_generator
        self.tile_collision_by_rect = tile_collision_by_rect
        self.sprites_collision_by_rect = sprites_collision_by_rect

    def __and__(self, other):
        if isinstance(other, Collider):
            complex_generator_obj = max(self, other, key=lambda x: x.manifold_generator.complexity)
            return Collider(
                not (self.sprites_collision_by_rect and other.sprites_collision_by_rect),
                not (self.tile_collision_by_rect and other.tile_collision_by_rect),  # uses the more complex system
                complex_generator_obj.manifold_generator,
            )
        return NotImplemented


class Tile(pygame.sprite.Sprite):
    id = 0
    blocks_list = pygame.sprite.Group()

    classes = {
    }

    @classmethod
    def get_tile(cls, id_):
        if 0 not in cls.classes:
            cls.classes[0] = Tile
        return cls.classes[id_]

    def __init_subclass__(cls, **kwargs):
        Tile.classes[cls.id] = cls

    def __init__(self, img: pygame.Surface, group: pygame_structures.TileCollection, *, x: int, y: int,
                 tile_collision_by_rect=True,
                 manifold_generator=Collider.empty_generator):
        super(Tile, self).__init__()
        self.image = img
        self.rect = img.get_rect()
        self.rect.topleft = x, y

        self.set_group(group)
        self.collider = Collider(False, tile_collision_by_rect, manifold_generator)
        self.elasticity = 1
        # self.mask = pygame.mask.from_surface(img)
        Tile.blocks_list.add(self)

    # @property
    # def position(self):
    #     return self.rect.center

    def set_group(self, group):
        if group is not None:
            self.group = group
            group.add_tile(self)
        else:
            c = pygame_structures.TileCollection()
            c.add_tile(self)
            self.group = c

    def sprite_collide(self, _sprite, collision: pygame_structures.collision_manifold):
        return _sprite.to_dict()

    def update(self):
        self.draw()

    def draw(self):
        pygame_structures.Camera.blit(self.image, self.rect.topleft - pygame_structures.Camera.scroller)

    @classmethod
    def update_all(cls):
        for platform in cls.blocks_list:
            platform.update()


class BlockingTile(Tile):
    id = 1

    def __init__(self, img, group: pygame_structures.TileCollection, restitution: float = 0.0,  static_friction: float = 0.0, dynamic_friction: float = 0.0,
                 *, x, y,):
        if group is None:
            group = self

        super(BlockingTile, self).__init__(img, x=x, y=y, group=group, manifold_generator=BaseSprite.basic_generator)
        self.max_stopping_friction = float('inf')  # change if want to simulate ice or something with low friction coeff
        # self.max_stopping_friction = 0  # change if want to simulate ice or something with low friction coeff

        self.dynamic_friction = 0  # not how real life friction works, but feels nice.
        self.static_friction = 0  # not how real life friction works, but feels nice.
        self.dynamic_friction = 0.15  # not how real life friction works, but feels nice.
        self.static_friction = 0.2  # not how real life friction works, but feels nice.
        self.restitution = restitution  # how "bouncy" the tile is, from zero to one

        self.normal = structures.Vector2.Zero()

    def sprite_collide(self, _sprite, manifold):
        # if not sprite.collide_mask(self, _sprite):
        #     return
        # print(self.rect.topleft)
        return
        before = super(BlockingTile, self).sprite_collide(_sprite, collision)

        # if not isinstance(_sprite, AdvancedSprite):
        #     return before
        try:
            if collision.contact_count > 0:
                contacts = collision.contact_points
            else:
                contacts = [None]

            for point in contacts:
                relative_velocity = _sprite.get_future_velocity(BaseSprite.game_states['dtime'])
                # relative_velocity = - _sprite.calculate_relative_velocity(self, point)

                # collision.normal = collision.normal * -1
                velocity_among_normal = relative_velocity * collision.normal

                if velocity_among_normal > 0:
                    return before

                if collision.x_collision:
                    was_on = _sprite.on_platform
                    _sprite.on_platform = self

                j = -(1 + self.restitution) * velocity_among_normal
                j /= 1 / float('inf') + 1 / _sprite.mass

                impulse = j * collision.normal

                self.friction(_sprite, collision, j)
                if not impulse:
                    return

                number_of_points = 1 if not collision.contact_count else collision.contact_count

                _sprite.apply_impulse(1 / _sprite.mass * impulse / number_of_points, point)

                # _sprite.add_force(impulse, 'normal', TrueSA)

                percent = 0.2
                slop = 0.01
                correction = max(collision.penetration - slop, 0.0) / (1 / _sprite.mass) * percent * collision.normal
                _sprite.position += 1 / _sprite.mass * correction

        except Exception as e:
            # pass
            raise e
            # print(e)
            # print(collision)

        return before

    def friction(self, _sprite, collision, j):
        t = _sprite.velocity - (_sprite.velocity * collision.normal) * collision.normal
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
        _sprite.update_velocity_and_acceleration(BaseSprite.game_states['dtime'])
        # print("changing velocity by:", frictionImpulse)


'''
    def friction(self, _sprite, collision, j):
        t = _sprite.velocity - (_sprite.velocity * collision.normal) * collision.normal
        if t:
            t.normalize()
        else:
            _sprite.update_velocity_and_acceleration(BaseSprite.game_states['dtime'])
            return
        jt = - (_sprite.velocity * t)
        jt *= _sprite.mass

        dynamic_friction = math.hypot(self.dynamic_friction, _sprite.dynamic_friction)
        frictionImpulse = -jt * t * dynamic_friction
        _sprite.add_force(- frictionImpulse, 'friction', False)
        _sprite.update_velocity_and_acceleration(BaseSprite.game_states['dtime'])
        # print("changing velocity by:", frictionImpulse)
        # _sprite.velocity -= (1 / _sprite.mass) * frictionImpulse

    def friction_old(self, _sprite, collision):
        velocity = _sprite.get_future_velocity(BaseSprite.game_states['dtime'])
        t = velocity - (velocity * collision.normal) * collision.normal
        if t:
            t.normalize()
        mu = math.hypot(self.static_friction, _sprite.static_friction)
        # print("sprite force is ", _sprite.force, t)
        # print(_sprite.force_document['sigma'], collision.normal, mu, normal)

        jt = - (_sprite.velocity * t)

        jt *= _sprite.mass

        if round(t * _sprite.velocity) == 0:
            if _sprite.force_document['sigma'] * t < collision.normal * mu * self.normal / BaseSprite.game_states['dtime']:
                frictionImpulse = structures.Vector2.Zero()
                _sprite.add_force((-_sprite.force_document['sigma'] * t) * t, 'static friction', False)
                _sprite.force_document['sigma'] = structures.Vector2.Zero()
        else:
            dynamic_friction = math.hypot(self.dynamic_friction, _sprite.dynamic_friction)
            frictionImpulse = -jt * t * dynamic_friction
            _sprite.add_force(- frictionImpulse, 'friction', False)
        # print("changing velocity by:", frictionImpulse)
        # _sprite.velocity -= (1 / _sprite.mass) * frictionImpulse
'''


class Spike(BlockingTile):
    id = 2

    def sprite_collide(self, _sprite, collision: pygame_structures.collision_manifold):
        if isinstance(_sprite, AdvancedSprite) and _sprite.resistance_timer:
            _sprite.hit_points -= 1
            _sprite.resistance_timer.activate()
        super(Spike, self).sprite_collide(_sprite, collision)


class Slime(BlockingTile):
    id = 4
    sur = pygame.image.load(os.path.dirname(__file__) + '\\images\\Slime_block.png')

    def __init__(self, size, *, x, y):
        sur = pygame.transform.smoothscale(self.sur, [size] * 2).convert_alpha()
        super(Slime, self).__init__(sur, restitution=0.7, static_friction=0.5, dynamic_friction=0.5, x=x, y=y)


class air(Tile):
    id = 3
    sur = pygame.Surface((0, 0))

    def __init__(self, *, x, y):
        super(air, self).__init__(air.sur, group=None, x=x, y=y)
        Tile.blocks_list.remove(self)

    def sprite_collide(self, _sprite, axis):
        pass

    def update(self):
        pass

    def draw(self):
        pass

    def __bool__(self):
        return False

    def set_group(self, group):
        pass

def by_two_objects(obj1, obj2):
    normal = get_mid(obj2) - get_mid(obj1)
    obj1_extent_x = obj1.rect.width / 2
    obj2_extent_x = obj2.rect.width / 2

    x_overlap = obj1_extent_x + obj2_extent_x - abs(normal.x)

    if x_overlap > 0:
        obj1_extent_y = obj1.rect.height / 2
        obj2_extent_y = obj2.rect.height / 2

        y_overlap = obj1_extent_y + obj2_extent_y - abs(normal.y)
        if y_overlap > 0:
            if x_overlap < y_overlap:
                if normal.x < 0:
                    normal_normalized = structures.Vector2.Cartesian(1, 0)
                else:
                    normal_normalized = structures.Vector2.Cartesian(-1, 0)
                penetration = x_overlap
            else:
                if normal.y < 0:
                    normal_normalized = structures.Vector2.Cartesian(0, 1)
                else:
                    normal_normalized = structures.Vector2.Cartesian(0, -1)
                penetration = y_overlap

            return CollisionManifold(None, normal_normalized, penetration, obj1, obj2, True)

    return CollisionManifold(None, None, 0, obj1, obj2, False)


def get_mid(obj):
    if isinstance(obj, BaseSprite):
        return obj.position
    else:  # Rect only no float position
        return obj.rect.center


class BaseSprite(pygame.sprite.Sprite):
    sprites_list = pygame.sprite.Group()
    image = pygame.Surface((100, 100))
    game_states = {'sprites': sprites_list, 'keys': [], 'dtime': 0}
    basic_generator = ManifoldGenerator(by_two_objects, 1)
    initiated = []

    def __init__(self, rect, control, mass, *, sprite_collision_by_rect=False, tile_collision_by_rect=True,
                 manifold_generator=Collider.empty_generator,
                 ):
        # hit boxes & moving
        if not self.__class__ in BaseSprite.initiated:

        super(BaseSprite, self).__init__()
        #
        self.collider = Collider(
            sprite_collision_by_rect,
            tile_collision_by_rect,
            manifold_generator
        )
        self.rect = rect
        if not hasattr(self, 'image'):
            self.image = pygame.Surface(self.rect)

        self.currently_colliding = []

        # physics
        self.on_platform = None
        self.position = structures.Vector2.Point(rect.center)
        self.velocity = structures.Vector2.Zero()
        self.acceleration = structures.Vector2.Zero()
        self.force = structures.Vector2.Zero()
        self.force_document = {}
        self.mass = mass

        self.static_friction = 0
        self.dynamic_friction = 0

        self.control = control

        self.restitution = 0
        BaseSprite.sprites_list.add(self)

    @classmethod
    def initiate(cls):
        pass

    @property
    def elasticity(self):
        return 1 - self.restitution

    @elasticity.setter
    def elasticity(self, value):
        self.restitution = 1 - value

    @property
    def inv_mass(self):
        return 1 / self.mass

    def apply_impulse(self, impulse, contact_point=None):
        self.velocity += impulse

    def to_dict(self):
        return {}

    def apply_gravity(self):
        self.add_force(structures.Vector2.Cartesian(0, GRAVITY * self.mass), 'gravity', False)

    def __call__(self):
        return self.rect.center

    def calculate_relative_velocity(self, other, contact_point):
        if isinstance(other, BaseSprite):
            other_vel = other.velocity
        elif isinstance(other, Tile):
            other_vel = structures.Vector2.Zero()
        return other_vel - self.velocity

    def draw_rect(self, clr=pygame.Color('red')):
        r = pygame.Rect(self.rect)
        r.topleft = r.topleft - pygame_structures.Camera.scroller
        pygame.draw.rect(pygame_structures.Camera.screen, clr, r, 1)

    def add_force(self, force: structures.Vector2, signature: str = None, mul_dtime: bool = True):
        """
        :param force : force to change acceleration (Vector2)
        :param signature: allows individual sprites class to ignore force from other sprites, e.g. ghost can avoid from
        :param mul_dtime: if True -> multiply the force by delta time
        getting normal force from walls
        """
        if mul_dtime:
            force = force / BaseSprite.game_states['dtime']
        self.force_document[signature] = force
        self.force += force
        self.force_document['sigma'] = self.force.copy()
        return force

    def debug(self, *args):
        string = ''
        for arg in args:
            string += arg + ': ' + str(eval(f'self.{arg}'))
            string += ', '
        print(string)

    def draw(self):
        """Called on redraw function for each sprite in BaseSprite.sprites_list.
         draw the sprite to the screen"""
        pygame_structures.Camera.blit(self.image, self.rect.topleft - pygame_structures.Camera.scroller)

    def _update(self, control_dict):
        """A method to control sprite behavior. Called ones per frame"""
        self.control.move(**control_dict)
        self.update_kinematics(control_dict['dtime'])
        self.update(control_dict)
        self.force_document = {}

    def update(self, control_dict):
        pass

    def update_acceleration(self):
        self.acceleration = (self.force / self.mass)  # Σ𝑓 = 𝓂 ⋅ 𝒶 -⋙ 𝒶 = Σ𝑓 / 𝓂

    def update_velocity(self, time_delta, axis=None):
        if axis is None:
            self.velocity += self.acceleration * time_delta
        elif axis == structures.Direction.horizontal:
            self.velocity.x += self.acceleration.x * time_delta
        elif axis == structures.Direction.vertical:
            self.velocity.y += self.acceleration.y * time_delta

    def update_position(self, time_delta):
        change = self.velocity * time_delta
        self.position += change
        self.rect.center = tuple(self.position.floor())
        return change

    def set_position(self, x=None, y=None):
        self.position.set_values(x, y)
        self.rect.center = tuple(self.position.floor())

    #

    def on_platform_collision(self, direction, platform, before):
        """Called when the sprite collides with a platform"""
        # when finishing the game, should try to change it to forced verision
        pass

    def update_kinematics(self, time_delta):
        platform, before = pygame_structures.Map.check_platform_collision(self, time_delta)
        if platform is not None:
            self.on_platform_collision(structures.Direction.vertical, platform, before)
            self.control.platform_collide(structures.Direction.vertical, platform, before)

        # print(self.force)
        self.update_position(time_delta)
        self.update_velocity_and_acceleration(time_delta)


        return platform

    def update_velocity_and_acceleration(self, time_delta):
        self.update_acceleration()
        self.update_velocity(time_delta)
        self.force.reset()

    def get_future_velocity(self, time_delta):
        return self.velocity + (self.force / self.mass) * time_delta

    @classmethod
    def check_sprite_collision(cls, collision_type='mask', *, lst=None):

        if lst is None:
            lst = cls.sprites_list
        if collision_type == 'mask':
            lst = list(lst)
            shuffle(lst)
            for idx, sprite1 in enumerate(lst):
                skip = idx + 1
                for sprite2 in lst:
                    if skip > 0:
                        skip -= 1
                        continue

                    collider: Collider = sprite1.collider & sprite2.collider
                    if pygame.sprite.collide_rect(sprite1, sprite2) and \
                            (collider.sprites_collision_by_rect or
                             pygame.sprite.collide_mask(sprite1, sprite2)):

                        manifold = collider.manifold_generator(sprite1, sprite2)
                        if (manifold is None) or manifold.collision:
                            block_second = sprite1.collision(sprite2)
                            sprite1.control.sprite_collide(sprite2)

                            if not block_second:
                                sprite2.collision(sprite1)
                                sprite2.control.sprite_collide(sprite1)

        elif collision_type == 'rect':
            raise
            for sprite1 in cls.sprites_list:
                for sprite2 in pygame.sprite.spritecollide(sprite1, cls.sprites_list, False):
                    if sprite2 is not sprite1:

                        block_second = sprite1.collision(sprite2)
                        sprite1.control.sprite_collide(sprite2)

                        if not block_second:
                            sprite2.collision(sprite1)
                            sprite2.control.sprite_collide(sprite1)

    @classmethod
    def update_all(cls):
        if cls.game_states['dtime'] == 0:
            return
        for sprt in cls.sprites_list:
            sprt._update(cls.game_states)

    @classmethod
    def update_states(cls, keys, time_delta):
        cls.game_states['dtime'] = time_delta
        cls.game_states['keys'] = keys

    def collision(self, other):
        """Called when one sprite collides with another
        """
        pass


class AdvancedSprite(BaseSprite):
    """Sprite that can jump and has health bar"""
    sprites_list = pygame.sprite.Group()
    image = pygame.Surface((100, 100))

    def __init__(self, rect, control, mass, hit_points,
                 health_bar_colors: Optional[Tuple[tuple, tuple]] = None, resistance_length=0):
        # hit boxes & moving
        super(AdvancedSprite, self).__init__(rect, control, mass)
        #

        # jumping & physics
        # Jumping
        self.base_hit_points = hit_points
        self.hit_points = self.base_hit_points
        self.resistance_timer = pygame_structures.Timer(resistance_length)
        self.is_dead = False
        self.visible = True

        if health_bar_colors is not None:
            self.health_bar = pygame_structures.HealthBar(*health_bar_colors, self)
        else:
            self.health_bar = None
        # self.stand_on_platform = False
        self.on_platform = False
        # physics
        self.velocity = structures.Vector2.Zero()
        self.acceleration = structures.Vector2.Zero()
        self.force = structures.Vector2.Zero()

        #  so the sprite will flicker when it has resistance
        self.alpha = -1
        self.delta_alpha = 1020  # brightness / second

        BaseSprite.sprites_list.add(self)

        # used for conditions
        self.sprite_collide = False  # Turn on when collides with sprite - used for conditions

    def draw_health_bar(self):
        if self.health_bar:
            self.health_bar.draw()

    def draw(self, draw_health=True):
        """Called on redraw function for each sprite in BaseSprite.sprites_list.
         draw the sprite to the screen"""
        if draw_health:
            self.draw_health_bar()

        if not self.resistance_timer.finished():
            # flickering
            if self.alpha == -1:
                self.alpha = 255
            self.image = self.image.copy()
            if not (0 < self.alpha < 255):
                self.delta_alpha *= -1

            self.alpha += self.delta_alpha * BaseSprite.game_states['dtime']
            self.image.set_alpha(self.alpha)
        elif not self.alpha == -1:  # first time after finished flickering
            self.alpha = -1
            self.delta_alpha = abs(self.delta_alpha)
            self.image.set_alpha(255)
        super(AdvancedSprite, self).draw()

    def _update(self, controls_dict):
        self.dead_check()
        super(AdvancedSprite, self)._update(controls_dict)
        self.force_document = {}

    def update_kinematics(self, time_delta):
        self.on_platform = super(AdvancedSprite, self).update_kinematics(time_delta)

    def collision(self, other):
        self.sprite_collide = other

    def dead_check(self):
        if self.hit_points <= 0 and not self.is_dead:
            self.is_dead = True
            self.die()
            return True
            # recommended to add a death sound
        return False

    def die(self):
        pass


def rigid_obb_generator(obj1, obj2):
    if isinstance(obj1, BaseRigidBody):
        self = obj1
        other = obj2
    else:
        self = obj2
        other = obj1

    self.obb.update_position(self.position, self.orientation)
    self_components = self.obb
    if isinstance(other, BaseRigidBody):
        other.obb.update_position(other.position, other.orientation)
        other_components = other.obb
    else:
        other_components = Bodies.AABB(other.rect)

    manifold = self.collision_detection(self_components, other_components)

    manifold.obj1 = self
    manifold.obj2 = other

    if manifold.collision:
        manifold.add_manifold(manifold)
    return True


class BaseRigidBody(BaseSprite):
    collision_jump_table = {}
    rigid_generator = ManifoldGenerator(rigid_obb_generator, 2)

    def __init__(self, rect, mass, moment_of_inertia, orientation, control=controls.NoMoveControl(), *,
                 calculate_attributes=False,
                 sprite_collision_by_rect=False,
                 tile_collision_by_rect=True,
                 manifold_generator=Collider.empty_generator):

        # super(BaseRigidBody, self).__init__(rect, control, mass, hit_points=hit_points,
        #                                     health_bar_colors=health_bar_colors)
        print("orientation is not one, make ur own obb")
        self.obb = Bodies.Rectangle.AxisAligned(rect.center, rect.width/2, rect.height/2, (0, 0), 0)
        if calculate_attributes:
            mass = self.obb.polygon.mass
            moment_of_inertia = self.obb.polygon.moment_of_inertia

        super(BaseRigidBody, self).__init__(rect, control, mass,
                                            sprite_collision_by_rect=sprite_collision_by_rect,
                                            tile_collision_by_rect=tile_collision_by_rect,
                                            manifold_generator=manifold_generator
                                            )
        self.moment_of_inertia = moment_of_inertia
        self.orientation = orientation
        self.angular_velocity = 0
        self.torque = 0

    # @property
    # def angular_velocity(self):
    #     return 0
    #
    # @angular_velocity.setter
    # def angular_velocity(self, value):
    #     if value != 0:
    #         print()

    def draw_bounding_box(self):
        self.obb.update_position(self.position, self.orientation)
        self.obb.redraw()

    def update_velocity_and_acceleration(self, time_delta):
        super(BaseRigidBody, self).update_velocity_and_acceleration(time_delta)
        self.angular_velocity += self.torque / self.moment_of_inertia

    def apply_impulse(self, impulse, contact_point=None):
        super(BaseRigidBody, self).apply_impulse(impulse, contact_point)
        if contact_point is not None:
            self.angular_velocity += ((self.position - contact_point) ** impulse) / self.moment_of_inertia

    def calculate_relative_velocity(self, other, contact_point):
        if contact_point:
            contact_point = structures.Vector2.Zero()
        radii_self = contact_point - self.position
        if isinstance(other, ImagedRigidBody):
            radii_other = contact_point - other.position
            other_angular_velocity = other.angular_velocity
        else:
            other_angular_velocity = 0
            radii_other = structures.Vector2.Zero()
        return super(BaseRigidBody, self).calculate_relative_velocity(other, contact_point) + \
               (math.radians(other_angular_velocity) ** radii_other) - \
               (math.radians(self.angular_velocity) ** radii_self)

    @property
    def inv_moment_of_inertia(self):
        return 1 / self.moment_of_inertia

    def update_position(self, time_delta):
        change = super(BaseRigidBody, self).update_position(time_delta)
        self.orientation += self.angular_velocity * time_delta
        return change

    @classmethod
    def collision_detection(cls, self: Bodies.Body, other: Bodies.Body):
        """
        Implemented using the separating axis theorem (SAT)
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
                        smallest_axis = smallest_axis * -1
                else:
                    vertex_object = self
                    if proj1.max < proj2.max:
                        smallest_axis = smallest_axis * -1

        contact_vertex = cls.projection_onto_axis(vertex_object, smallest_axis).collision_vertex

        if vertex_object is other:
            smallest_axis = smallest_axis * -1

        # pygame_structures.Camera.add_blit_order(lambda: draw_circle(contact_vertex, 10, 2), .03)

        return CollisionManifold(contact_vertex, smallest_axis, min_overlap, None, None, True, solve=False)

    @staticmethod
    def projection_onto_axis(obj: Bodies.Body, axis: structures.Vector2):
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


class ImagedRigidBody(BaseRigidBody):
    def __init__(self, image, rect, mass, moment_of_inertia, orientation, control=controls.NoMoveControl(),
                 rotation_offset=None):
        super(ImagedRigidBody, self).__init__(rect, mass, moment_of_inertia, orientation, control)
        self.generate_collision_manifold = True

        if rotation_offset is None:
            rotation_offset = tuple(structures.Vector2.Point(image.get_size()) / 2)

        self.real_image = pygame_structures.RotatableImage(image, orientation, rotation_offset)

    def draw(self):
        self.real_image.rotate(int(self.orientation))
        self.image, origin = self.real_image.blit_image(self.position.floor())
        # try:
        #     pygame.draw.circle(pygame_structures.Camera.screen, pygame.Color('red'), tuple(self.com_position.floor()), 2)
        #     pygame.draw.circle(pygame_structures.Camera.screen, pygame.Color('red'), tuple(self.position.floor()), 2)
        # except Exception as e:
        #     print(self.com_position)
        #     raise e
        # center = self.rect.center

        new = self.rect.copy()
        new.size = self.real_image.edited_img.get_size()
        new.center = self.rect.center
        # self.rect.size = self.real_image.edited_img.get_size()
        # self.rect.center = center

        self.rect.topleft = tuple(
            self.rect.topleft - (structures.Vector2.Point(new.size) - structures.Vector2.Point(self.rect.size)) / 2
        )
        self.rect.size = new.size
        # self.draw_rect()

    def generate_manifold(self, other: Union[Tile, BaseSprite, pygame.sprite.Sprite]):
        pass


class DrivableSprite(AdvancedSprite):
    def __init__(self, rect, control, mass, hit_points,
                 health_bar_colors: Optional[Tuple[tuple, tuple]] = None, resistance_length=0):
        super(DrivableSprite, self).__init__(rect, control, mass, hit_points, health_bar_colors, resistance_length)
        self.vehicle = None

    def _update(self, controls_dict):
        if self.vehicle is None:
            super(DrivableSprite, self)._update(controls_dict)
        else:
            self.rect.topleft = self.vehicle.get_sprite_position()  # update position to vehicle position
            self.set_position()

    def collision(self, other):
        if isinstance(other, Vehicle):
            return True


class Vehicle(AdvancedSprite):
    def __init__(self, rect, control, mass, sprite_position, hp,
                 health_bar_colors: Optional[Tuple[tuple, tuple]] = None):
        super(Vehicle, self).__init__(rect, control, mass, hp, health_bar_colors)
        self.sprite = None
        self.sprite_position = sprite_position

    def set_sprite(self, sprt):
        self.sprite = sprt

    def get_sprite_position(self):
        return self.sprite_position


class Bullet(BaseSprite):
    DAMAGE = 1

    def __init__(self, rect, damage, travel_distance):
        super(Bullet, self).__init__(rect, controls.NoMoveControl(), 1)
        self.damage = damage
        self.travel_distance = travel_distance
        self.first_frame = True

    def __str__(self):
        return super(Bullet, self).__str__() + f', travel_distance{self.travel_distance}'

    def update_position(self, time_delta):
        if self.travel_distance <= 0:
            self.kill()
        self.travel_distance -= abs(self.velocity * time_delta)
        super(Bullet, self).update_position(time_delta)

    def collision(self, other):
        if self.first_frame:
            self.first_frame = False
            return
        if isinstance(other, AdvancedSprite) and not other.is_dead:
            if other.resistance_timer.finished():
                other.hit_points -= self.damage
                other.resistance_timer.activate()
            self.kill()
            return True
            # Camera.shake()
        # elif isinstance(other, Bullet):

    def on_platform_collision(self, direction, platform, before):
        if direction == structures.Direction.vertical:
            self.kill()


class Magazine(pygame.sprite.Group):
    magazines_list = []

    def __init__(self, clr, size, shot_delay, capacity, damage=Bullet.DAMAGE):
        super(Magazine, self).__init__()
        self.capacity = capacity
        self.shot_timer = pygame_structures.Timer(shot_delay)
        self.color = clr
        self.size = size
        self.damage = damage
        Magazine.magazines_list.append(self)

    def add_bullet(self, x, y, velocity_vector, clr=None, size=None, damage=None):
        if self.shot_timer.finished() and not self.full():
            self.shot_timer.activate()
            bull = GunBullet(maybe(clr).or_else(self.color),
                             maybe(size).or_else(self.size),
                             x, y,
                             maybe(damage).or_else(self.damage))
            bull.add_force(velocity_vector, "shoot")
            self.add(bull)
            return bull
        return None

    def full(self):
        return len(self) == self.capacity


class GunBullet(Bullet):
    DAMAGE = 1
    SPEED = 500
    TRAVEL_DISTANCE = 1000

    def __init__(self, clr, size, x, y, damage=DAMAGE, travel_distance=TRAVEL_DISTANCE):
        try:
            self.right_image = pygame.image.load(os.path.join(r'animation\bullet', size, clr) + '.png').convert_alpha()
            self.left_image = pygame.transform.flip(self.right_image, True, False).convert_alpha()
        except pygame.error:
            raise AttributeError('invalid color or size. color can be green, yellow, blue or red; size can be small,'
                                 'medium or large')
        size = 2
        self.right_image = pygame.transform.smoothscale(self.right_image, (self.right_image.get_width() * size,
                                                                           self.right_image.get_height() * size)).convert_alpha()
        self.left_image = pygame.transform.smoothscale(self.left_image, (self.left_image.get_width() * size,
                                                                         self.left_image.get_height() * size)).convert_alpha()
        rect = self.right_image.get_rect()
        rect.topleft = x, y
        super(GunBullet, self).__init__(rect, damage, travel_distance)

    def draw(self):
        if self.velocity.x > 0:
            self.image = self.right_image
        else:
            self.image = self.left_image
        super(GunBullet, self).draw()
        # self.draw_rect()

    @staticmethod
    def get_image_size(clr, size):
        try:
            size = pygame.image.load(os.path.join(r'animation\bullet', size, clr) + '.png').get_size()
            return size[0] * 2, size[1] * 2
        except pygame.error:
            raise AttributeError('invalid color or size. color can be green, yellow, blue or red; size can be small,'
                                 'medium or large')


def resolve_collisions():
    for manifold in CollisionManifold.Manifolds:
        manifold.collision_response()

    for manifold in CollisionManifold.Manifolds:
        manifold.penetration_resolution()
    CollisionManifold.Manifolds.clear()


def solve_manifolds(n=1):
    if n > 0:
        sprites_set = set()
        for m in CollisionManifold.Manifolds:
            sprites_set.add(m.obj1)
            sprites_set.add(m.obj2)
    resolve_collisions()
    for i in range(n - 1):
        BaseSprite.check_sprite_collision(lst=sprites_set)
        resolve_collisions()


def tick(elapsed, keys=pygame.key.get_pressed()):
    # print(len(BaseSprite.sprites_list))
    start = time()
    BaseSprite.update_states(keys, elapsed)
    pygame_structures.Camera.reset_frame()
    # BaseSprite.check_sprite_collision()
    Particles.Particle.check_all_collision(BaseSprite.sprites_list)
    BaseSprite.update_all()
    BaseSprite.check_sprite_collision()

    solve_manifolds()

    for s in BaseSprite.sprites_list:
        s.draw()

    Particles.Particle.update_all()
    Tile.update_all()
    pygame_structures.Camera.scroller.update()
    structures.UntilCondition.update_all()

import warnings

from Engine.CollisionManifold import ManifoldGenerator, CollisionManifold
import Engine.base_control as controls
import Engine.Particle as Particles
import Engine.structures as structures
from collections import namedtuple
from typing import Tuple, Optional
from Engine import Sound, Bodies
from random import shuffle
from Engine.Debug import *
from time import time
import pygame
import math
import os

Projection = namedtuple('Projection', ('min', 'max', 'collision_vertex'))
player = Sound.Player()
clock = pygame.time.Clock()
GRAVITY = 3_000
GRAVITY = 1_500

# GRAVITY = 150
# GRAVITY = 20


def no_generator(a, b):
    """
    Empty manifold generator
    """
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
        """
        Combines two Collider objects into one, choosing the more complex one from every aspect
        :param other:
        :return:
        """
        if isinstance(other, Collider):
            complex_generator_obj = max(self, other, key=lambda x: x.manifold_generator.complexity)
            return Collider(
                self.sprites_collision_by_rect and other.sprites_collision_by_rect,
                self.tile_collision_by_rect and other.tile_collision_by_rect,  # uses the more complex system
                complex_generator_obj.manifold_generator,
            )
        return NotImplemented


class Tile(pygame.sprite.Sprite):
    id = 0
    blocks_list = pygame.sprite.Group()

    classes = {
    }

    # image = pygame_structures.PrivateAutoConvertSurface(False)

    @classmethod
    def get_tile(cls, id_):
        """
        Get tile class by id
        :param id_:  id of tile class
        :return:  class with id == id_
        """
        if 0 not in cls.classes:
            cls.classes[0] = Tile
        return cls.classes[id_]

    def __init_subclass__(cls, **kwargs):
        """
        Sets an id to each subclass
        """
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
        self.mask = pygame.mask.from_surface(img)
        Tile.blocks_list.add(self)

    def set_group(self, group):
        """
        Sets tile's group to group
        :param group:
        :return:
        """
        if group is not None:
            self.group = group
            group.add_tile(self)
        else:
            c = pygame_structures.TileCollection()
            c.add_tile(self)
            self.group = c

    def sprite_collide(self, sprite, collision: CollisionManifold):
        """
        Called when sprite collides with tile
        :param sprite: other sprite
        :param collision: collision manifold
        """

    def _update(self):
        """
        Called each frame to update self's attributes.
        """
        self.draw()

    def update(self):
        """
        Called each frame, meant to control the tile's behavior (by overriding).
        """

    def draw(self):
        """
        Draws the tile to the screen
        """
        pygame_structures.Camera.blit(self.image, self.rect.topleft - pygame_structures.Camera.scroller)

    def draw_rect(self, clr=pygame.Color('red')):
        """
        Draw tile's hitbox
        :param clr: rectangle color
        """
        if not pygame_structures.Camera.screen:
            return
        r = pygame.Rect(self.rect)
        r.topleft = r.topleft - pygame_structures.Camera.scroller
        pygame.draw.rect(pygame_structures.Camera.screen, clr, r, 0)

    @classmethod
    def update_all(cls):
        """
        Updates all tiles (called each frame)
        """
        for platform in cls.blocks_list:
            platform._update()


class BlockingTile(Tile):
    id = 1

    def __init__(self, img, group: pygame_structures.TileCollection, restitution: float = 0.0,  static_friction: float = 0.0, dynamic_friction: float = 0.0,
                 *, x, y,):
        super(BlockingTile, self).__init__(img, x=x, y=y, group=group, manifold_generator=BaseSprite.basic_generator,
                                           )
        self.dynamic_friction = 0.15  # not how real life friction works, but feels nice.
        self.static_friction = 0.2  # not how real life friction works, but feels nice.
        self.restitution = restitution  # how "bouncy" the tile is, from zero to one (coefficient of restitution)


class Spike(BlockingTile):
    id = 2

    def sprite_collide(self, _sprite, collision: CollisionManifold):
        if isinstance(_sprite, AdvancedSprite) and _sprite.resistance_timer:
            _sprite.hit_points -= 1
            _sprite.resistance_timer.activate()
        super(Spike, self).sprite_collide(_sprite, collision)


class Slime(BlockingTile):
    id = 4
    sur = pygame.image.load(os.path.dirname(__file__) + '\\images\\Slime_block.png')

    def __init__(self, group, *, x, y):
        size = pygame_structures.Map.instance.tile_size
        sur = pygame.transform.smoothscale(self.sur, [size] * 2).convert_alpha()
        super(Slime, self).__init__(sur, group, restitution=0.7, static_friction=0.5, dynamic_friction=0.5, x=x, y=y)


class air(Tile):
    id = 3
    sur = pygame.Surface((0, 0))

    def __init__(self, *, x, y):
        super(air, self).__init__(air.sur, group=None, x=x, y=y)
        Tile.blocks_list.remove(self)

    def sprite_collide(self, _sprite, axis):
        pass

    def _update(self):
        pass

    def draw(self):
        pass

    def __bool__(self):
        return False

    def set_group(self, group):
        pass


def by_two_objects(obj1, obj2):
    """
    The simplest manifold generator - generates a manifold using two objects' hitboxes.
    """
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
    """
    Returns the COM of a sprite
    """
    if isinstance(obj, BaseSprite):
        return obj.position
    else:  # Rect only no float position
        return obj.rect.center


class MetaSprite(type):
    sprites_list = pygame.sprite.Group()

    def __call__(cls, *args, **kwargs):
        """Called when you call BaseSprite()"""
        obj = type.__call__(cls, *args, **kwargs)
        obj.final_initiation()
        return obj


class BaseSprite(pygame.sprite.Sprite, metaclass=MetaSprite):
    collision_detection = True
    current_id = 0

    sprites_by_id = {}

    image = pygame.Surface((100, 100))
    game_states = {'sprites': MetaSprite.sprites_list, 'keys': [], 'dtime': 0}
    basic_generator = ManifoldGenerator(by_two_objects, 1)

    id = 1
    blocks_list = pygame.sprite.Group()

    classes = {
    }

    server = None
    client = None

    @classmethod
    def create_from_kwargs(cls, *, id_, **kwargs):
        """
        Creates a sprite from the given kwargs
        :param id_: id of sprite
        :param kwargs: kwargs for initiation
        :return: Instance of cls
        """
        return cls(**kwargs)

    @classmethod
    def get_sprite_class(cls, id_):
        """
        :return: Sprite class by id
        """
        if '0' not in cls.classes:
            cls.classes['0'] = BaseSprite
        return cls.classes[id_]

    @classmethod
    def set_server(cls, server):
        """
        Sets server attribute
        """
        cls.server = server

    @classmethod
    def set_client(cls, client):
        """
        Sets client attribute
        """
        cls.client = client

    def __init_subclass__(cls, **kwargs):
        """
        Called when BaseSprite is inherited. Assigns a unique id for each.
        """
        cls.id = BaseSprite.id
        BaseSprite.classes[str(cls.id)] = cls
        BaseSprite.id += 1

    def __init__(self, rect, control: controls.BaseControl, mass, *, sprite_collision_by_rect=False, tile_collision_by_rect=True,
                 manifold_generator=Collider.empty_generator
                 ):

        self.initiated = False

        self.user = None

        # hit boxes & moving
        if control is None:
            control = controls.NoMoveControl()
        super(BaseSprite, self).__init__()

        #
        self.collider: Collider = Collider(
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
        self.restitution = 0

        self.control: controls.BaseControl = control

        self.child_sprites = []

        self.current_collisions = set()
        self._frame_collisions = set()

        self.id = BaseSprite.current_id
        BaseSprite.current_id += 1
        if str(self.id) not in BaseSprite.sprites_by_id:
            BaseSprite.sprites_by_id[str(self.id)] = self
        else:
            pass
            # warnings.warn('id occupied?!')

    def final_initiation(self):
        """
        Called after a sprite is initiated. Adds it to the sprite's list (so it won't be updated before it's ready)
        """
        self.initiated = True
        if self.id is not None:
            BaseSprite.sprites_list.add(self)

        for sprite in self.child_sprites:
            if sprite in BaseSprite.sprites_list:
                BaseSprite.sprites_list.remove(sprite)
            BaseSprite.sprites_list.add(sprite)

    def add_child(self, child):
        """
        Adds a child to self. (Child is a sprite that is accompanied by another.
         It doesn't have it's own id and it's updated by it's parent)
        :param child: child sprite
        """
        self.child_sprites.append(child)
        child.set_id(None)

    def add_to_server(self, controller, **kwargs):
        """
        Adds a sprite to the server post-creation
        :param controller: Sprite's user
        :param kwargs: kwargs used to create self
        """
        if self.server is not None:
            self.server.add_sprite(self, controller, **kwargs)

    @classmethod
    def create_and_add_to_server(cls, controller, **kwargs):
        """
        Creates a sprite, then adds it to the server.
        :param controller: Sprite's user
        :param kwargs: kwargs used to create the sprite
        :return: New sprite
        """
        sprite = cls(**kwargs)
        sprite.add_to_server(controller, **kwargs)
        return sprite

    def set_user(self, user):
        """
        Sets sprite user (controller)
        :param user: User or OtherUser
        """
        self.user = user
        for child in self.child_sprites:
            child.set_user(user)

    def set_id(self, id_):
        """
        Sets sprite's id to id_
        :param id_:
        :return:
        """
        if self.id == id_:
            return
        if str(id_) in BaseSprite.sprites_by_id:
            warnings.warn(str(self) + '\t' + 'id occupied?! by ' + str(BaseSprite.sprites_by_id[str(id_)]))

        if BaseSprite.sprites_by_id[str(self.id)] is self:
            BaseSprite.sprites_by_id.pop(str(self.id))
        self.id = id_
        BaseSprite.sprites_by_id[str(self.id)] = self

    def encode(self) -> dict:
        """
        Encode self to a dict that can be sent over socket.
        It is sent from server to client with the command "Update".
        :return: A dict that can be sent over socket
        """
        x = self.position.floor()
        v = self.velocity.floor()
        return {'x': x.encode(), 'v': v.encode()}

    def decode_update(self, **kwargs):
        """
        Decodes the dict made by the encode method and updates self accordingly
        :param kwargs: dict made by the encode method
        """
        new_position = structures.Vector2.decode(kwargs['x'])
        new_velocity = structures.Vector2.decode(kwargs['v'])
        self.position.set_values(*new_position)
        self.velocity.set_values(*new_velocity)

    @classmethod
    def encode_creation(cls, **kwargs):
        """
        Similar to the encode method, but encode information about sprite's *initiation*.
        :param kwargs: Real creation arguments
        :return: Encoded creation arguments
        """
        return kwargs

    @classmethod
    def decode_creation(cls, **kwargs):
        """
        Similar to the decode method, but decode the information encoded by "encode_creation".
        This method does NOT create a sprite from the decoded information. Just returns it
        :param kwargs: Encoded creation arguments
        :return: Real creation arguments
        """
        return kwargs

    @property
    def inv_mass(self):
        """
        Inverse mass
        """
        return 1 / self.mass

    def apply_impulse(self, impulse, contact_point=None):
        """
        Applies an impulse vector "impulse" to self.
        :param impulse: Vector2 which represents the impulse
        :param contact_point: Where the impulse took place
            (only matters when accounting for rotation - BaseRigidBody class)
        """
        self.velocity += impulse / self.mass

    def apply_gravity(self):
        """
        Applies gravitational force on self.
        """
        self.add_force(structures.Vector2.Cartesian(0, GRAVITY * self.mass), 'gravity', False)

    def __call__(self):
        """
        :return: Position of self.
        """
        return self.rect.center

    def calculate_relative_velocity(self, other, contact_point):
        """
        Calculates the relative velocity between self and other.
        :param other: The second sprite
        :param contact_point: A point to calculate the relative velocity at
            (only matters when accounting for rotation - BaseRigidBody class)
        """
        if isinstance(other, BaseSprite):
            other_vel = other.velocity
        elif isinstance(other, Tile):
            other_vel = structures.Vector2.Zero()
        return other_vel - self.velocity

    def draw_rect(self, clr=pygame.Color('red'), w=1):
        """
        Draw the sprite's hitbox
        :param clr: hitbox color
        :param w: width of the hitbox
        """
        if 1 in self.rect.size:
            pygame.draw.line(pygame_structures.Camera.screen, clr, self.rect.topleft, self.rect.bottomright, w)
        else:
            r = pygame.Rect(self.rect)
            r.topleft = r.topleft - pygame_structures.Camera.scroller
            pygame.draw.rect(pygame_structures.Camera.screen, clr, r, w)

    def add_force(self, force: structures.Vector2, signature: str = None, mul_dtime: bool = True):
        """
        Adds a force to accelerate self.
        :param force : force to change acceleration (Vector2)
        :param signature: allows individual sprites class to ignore force from other sprites, e.g. ghost can avoid from
        :param mul_dtime: if True -> multiply the force by delta time (So force is actually difference in velocity)
        getting normal force from walls
        """
        if mul_dtime:
            force = force / BaseSprite.game_states['dtime']
        self.force_document[signature] = force
        self.force += force
        self.force_document['sigma'] = self.force.copy()
        return force

    def debug(self, *args):
        """
        Prints requested self's attributes. Used for debugging purposes (Debug mode is for the weak)
        :param args: list of attributes to print
        :return:
        """
        string = ''
        for arg in args:
            string += arg + ': ' + str(self.__getattribute__(arg))
            string += ', '
        print(string)

    def draw(self):
        """
        Called on redraw function for each sprite in BaseSprite.sprites_list.
        draw the sprite to the screen
        """
        pygame_structures.Camera.blit(self.image, self.rect.topleft - pygame_structures.Camera.scroller)

    def _update(self, control_dict):
        """A method to control sprite behavior. Called ones per frame"""
        if self.user is not None:
            control_dict = control_dict.copy()
            control_dict['keys'] = self.user.active_keys

        self.control.move(**control_dict)
        self.update_kinematics(control_dict['dtime'])
        self.update(control_dict)
        self.force_document = {}

    def update(self, control_dict):
        """A method to control sprite behavior. Called ones per frame. Meant to be overridden.
        :param control_dict: A dictionary containing the current game_states (dt, pressed keys, sprites list)
        """

    def update_acceleration(self):
        """
        Updates the acceleration by newton second law. Called once per frame
        """
        self.acceleration = (self.force / self.mass)  # Σ𝑓 = 𝓂 ⋅ 𝒶 -⋙ 𝒶 = Σ𝑓 / 𝓂

    def update_velocity(self, time_delta):
        """
        Updates sprite's velocity by it's acceleration. Called once per frame
        :param time_delta: elapsed time from last frame
        """
        self.velocity += self.acceleration * time_delta

    def update_position(self, time_delta):
        """
        Updates sprite's position by it's velocity and updates the hitbox. Called once per frame.
        :param time_delta: elapsed time from last frame
        :return: Difference in position from last frame
        """
        change = self.velocity * time_delta
        self.set_position(*(self.position + change))
        return change

    def set_position(self, x=None, y=None):
        """
        Sets sprites position to x and y
        :param x: x position value
        :param y: y position value
        """
        self.position.set_values(x, y)
        self.rect.center = tuple(round(self.position))

    def on_platform_collision(self, platform):
        """Called when the sprite collides with a platform"""

    def update_kinematics(self, time_delta):
        """
        Updates sprite's kinematic values and check for collision with the tiles.
        :param time_delta: elapsed time from last frame
        :return: one (if any) of the platform the sprite has collided with.
        """
        if self.collision_detection:
            platform = pygame_structures.Map.check_platform_collision(self)
            if platform is not None:
                self.on_platform_collision(platform)
                self.control.platform_collide(platform)

        self.update_position(time_delta)
        self.update_velocity_and_acceleration(time_delta)

        if self.collision_detection:
            return platform

    def update_velocity_and_acceleration(self, time_delta):
        """Update sprite's velocity and acceleration. then reset force"""
        self.update_acceleration()
        self.update_velocity(time_delta)
        self.force.reset()

    def get_future_velocity(self, time_delta):
        """Returns the velocity of sprite on the next frame"""
        return self.velocity + (self.force / self.mass) * time_delta

    @classmethod
    def check_sprite_collision(cls, *, lst=None):
        """
        Checks and tests for sprites collision.
        :param lst: list of sprites (None means BaseSprite.sprites_list)
        """
        if not cls.collision_detection:
            return
        if lst is None:
            lst = cls.sprites_list
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

                        sprite1.add_collision(sprite2)
                        sprite2.add_collision(sprite1)

                        block_second = sprite1.collision(sprite2)
                        sprite1.control.sprite_collide(sprite2)

                        if not block_second:
                            sprite2.collision(sprite1)
                            sprite2.control.sprite_collide(sprite1)

    @classmethod
    def update_all(cls):
        """Updates all sprites"""
        if cls.game_states['dtime'] == 0:
            return
        for sprt in cls.sprites_list:
            sprt._update(cls.game_states)

    @classmethod
    def update_states(cls, keys, time_delta):
        """Update game states. Called at the beginning of each frame"""
        cls.game_states['dtime'] = time_delta
        cls.game_states['keys'] = keys

    def collision(self, other):
        """Called when one sprite collides with another"""

    def solved_collision(self, other):
        """Called after a collision manifold is solved"""

    def add_collision(self, other):
        self._frame_collisions.add(other)

    @classmethod
    def replace_current_collisions(cls):
        """Resets all sprites' current collisions"""
        sprite: BaseSprite
        for sprite in cls.sprites_list:
            sprite.current_collisions = sprite._frame_collisions
            sprite._frame_collisions = set()

    def kill(self) -> None:
        if self.server and self.id is not None:
            self.server.kill_sprite(self.id)
        super(BaseSprite, self).kill()


class AdvancedSprite(BaseSprite):
    """Sprite that have hp (including resistance timer and health bar)"""
    sprites_list = pygame.sprite.Group()
    image = pygame.Surface((100, 100))

    def __init__(self, rect, control, mass, hit_points,
                 health_bar_colors: Optional[Tuple[tuple, tuple]] = None, resistance_length=0):
        super(AdvancedSprite, self).__init__(rect, control, mass,
                                             manifold_generator=BaseSprite.basic_generator)

        # Hitpoints
        self.base_hit_points = hit_points
        self.hit_points = self.base_hit_points
        self.resistance_timer = pygame_structures.Timer(resistance_length)
        self.is_dead = False
        self.visible = True

        if health_bar_colors is not None:
            self.health_bar = pygame_structures.HealthBar(*health_bar_colors, self)
        else:
            self.health_bar = None

        # flickering effect of the sprite when it has resistance
        self.alpha = -1
        self.delta_alpha = 1020  # brightness / second

    def encode(self):
        d = super(AdvancedSprite, self).encode()
        d['hp'] = str(self.hit_points)
        return d

    def decode_update(self, **kwargs):
        super(AdvancedSprite, self).decode_update(**kwargs)
        self.hit_points = int(kwargs['hp'])

    def draw_health_bar(self):
        """Draws the health bar"""
        if self.health_bar:
            self.health_bar.draw()

    def draw(self, draw_health=True):
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

    def dead_check(self):
        """Checks if sprite is dead. If it is it kills it"""
        if self.hit_points <= 0 and not self.is_dead:
            self.is_dead = True
            self.die()
            return True
            # recommended to add a death sound
        return False

    def die(self):
        """Called when the sprite is out of HP. Recommended way of handling it is adding a dying animation"""
        self.kill()


def rigid_obb_generator(obj1, obj2):
    """Generates a collision manifold with two object, Using two OBB's as hitboxes"""
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
                 manifold_generator=Collider.empty_generator,
                 obb_orientation=0):

        warnings.warn("orientation is not one, make ur own obb")
        self.obb = Bodies.Rectangle.AxisAligned(rect.center, rect.width / 2, rect.height / 2, (0, 0), obb_orientation)
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

    def draw_bounding_box(self):
        """Similar to BaseSprite draw_rect method but draws an OBB instead"""
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
        """
        :param obj: sprite
        :param axis: 2D Unit Vector
        :return: The projection of "sprite" on the axis "axis"
        """
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

    def encode(self):
        d = super(BaseRigidBody, self).encode()
        d['av'] = str(int(self.angular_velocity % 360))
        d['a'] = str(int(self.orientation % 360))
        return d

    def decode_update(self, **kwargs):
        super(BaseRigidBody, self).decode_update(**kwargs)
        self.angular_velocity = int(kwargs['av'])
        self.orientation = int(kwargs['a'])


class ImagedRigidBody(BaseRigidBody):
    def __init__(self, image, rect, mass, moment_of_inertia, orientation, control=controls.NoMoveControl(),
                 rotation_offset=None):
        super(ImagedRigidBody, self).__init__(rect, mass, moment_of_inertia, orientation, control)

        if rotation_offset is None:
            rotation_offset = tuple(structures.Vector2.Point(image.get_size()) / 2)

        self.real_image = pygame_structures.RotatableImage(image, orientation, rotation_offset)

    def draw(self):
        self.real_image.rotate(int(self.orientation))
        self.image, origin = self.real_image.blit_image(self.position.floor())

        new = self.rect.copy()
        new.size = self.real_image.edited_img.get_size()
        new.center = self.rect.center

        self.rect.topleft = tuple(
            self.rect.topleft - (structures.Vector2.Point(new.size) - structures.Vector2.Point(self.rect.size)) / 2
        )
        self.rect.size = new.size


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

    def set_sprite(self, sprite: DrivableSprite):
        """Sets the driver of the vehicle"""
        self.sprite = sprite

    def get_sprite_position(self):
        """Get global sprite position"""
        return self.sprite_position


class Bullet(BaseSprite):
    DAMAGE = 1

    def __init__(self, rect, damage, travel_distance):
        super(Bullet, self).__init__(rect, controls.NoMoveControl(), 1, tile_collision_by_rect=False)
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

    def on_platform_collision(self, platform):
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
        """Adds a bullet to the magazine"""
        if self.shot_timer.finished() and not self.full():
            self.shot_timer.activate()
            bull = GunBullet(clr or self.color,
                             size or self.size,
                             x, y,
                             damage or self.damage)
            bull.add_force(velocity_vector, "shoot")
            self.add(bull)
            return bull
        return None

    def full(self):
        """Returns true if the magazine is full, false otherwise"""
        return len(self) == self.capacity


class GunBullet(Bullet):
    DAMAGE = 1
    SPEED = 500
    TRAVEL_DISTANCE = 1000
    SCALE = 2

    def __init__(self, clr, x, y, size=SCALE, damage=DAMAGE, travel_distance=TRAVEL_DISTANCE):
        try:
            self.right_image = pygame.image.load(os.path.join(r'animation\bullet', size, clr) + '.png').convert_alpha()
            self.left_image = pygame.transform.flip(self.right_image, True, False).convert_alpha()
        except pygame.error:
            raise AttributeError('invalid color or size. color can be green, yellow, blue or red; size can be small,'
                                 'medium or large')
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

    @classmethod
    def get_image_size(cls, clr, size):
        """Returns the default image size of a bullet """
        try:
            size = pygame.image.load(os.path.join(r'animation\bullet', size, clr) + '.png').get_size()
            return size[0] * cls.SCALE, size[1] * cls.SCALE
        except pygame.error:
            raise AttributeError('invalid color or size. color can be green, yellow, blue or red; size can be small,'
                                 'medium or large')


def resolve_collisions():
    """Solves current open manifolds"""
    for manifold in CollisionManifold.Manifolds:
        manifold.collision_response()

    for manifold in CollisionManifold.Manifolds:
        manifold.penetration_resolution()
        if isinstance(manifold.obj1, BaseSprite):
            manifold.obj1.solved_collision(manifold.obj2)
        if isinstance(manifold.obj2, BaseSprite):
            manifold.obj2.solved_collision(manifold.obj1)
    CollisionManifold.Manifolds.clear()


def solve_manifolds(n=10):
    """Solves and checks for collisions n times"""
    if n > 0:
        sprites_set = set()
        for m in CollisionManifold.Manifolds:
            f = lambda obj: obj.reference if isinstance(obj, pygame_structures.TileCollection) else obj
            if isinstance(f(m.obj1), Tile) or isinstance(f(m.obj2), Tile): continue
            sprites_set.add(f(m.obj1))
            sprites_set.add(f(m.obj2))
    resolve_collisions()
    for i in range(n - 1):
        BaseSprite.check_sprite_collision(lst=sprites_set)
        if not CollisionManifold.Manifolds:
            break
        resolve_collisions()


def tick(elapsed, keys=pygame.key.get_pressed()):
    """A frame of the physics engine"""
    start = time()
    BaseSprite.update_states(keys, elapsed)
    pygame_structures.Camera.reset_frame()

    Particles.Particle.check_all_collision(BaseSprite.sprites_list)
    BaseSprite.update_all()
    BaseSprite.check_sprite_collision()

    solve_manifolds()

    if pygame_structures.Camera.real_screen:
        for s in BaseSprite.sprites_list:
            s.draw()

    BaseSprite.replace_current_collisions()

    Particles.Particle.update_all()
    Tile.update_all()
    pygame_structures.Camera.scroller.update()
    structures.UntilCondition.update_all()


def basic_loop():
    """Most basic main loop - runs the engine, controls client and check for exit events"""
    running = 1
    fps = 1000
    elapsed = 1/fps
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0

            if BaseSprite.client:
                if event.type == pygame.KEYDOWN:
                    BaseSprite.client.key_event(event.key, 1)

                if event.type == pygame.KEYUP:
                    BaseSprite.client.key_event(event.key, 0)

        keys = pygame.key.get_pressed()
        tick(elapsed, keys)

        pygame_structures.Camera.post_process(BaseSprite.sprites_list)
        elapsed = min(clock.tick(fps) / 1000.0, 1 / 30)

    if BaseSprite.server:
        print(BaseSprite.server)
        BaseSprite.server.server_socket.close()
    elif BaseSprite.client:
        BaseSprite.client.socket.close()



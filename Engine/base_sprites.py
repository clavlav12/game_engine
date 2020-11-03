import Engine.base_control as controls
import Engine.Particle as Particles
import Engine.structures as structures
import Engine.pygame_structures as pygame_structures
from Engine import Sound
import pygame
from typing import Tuple, Optional
from pymaybe import maybe
from numpy import sign
from time import time
import os

player = Sound.Player()
clock = pygame.time.Clock()
GRAVITY = 3_000


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

    def __init__(self, img: pygame.Surface, x: int, y: int):
        super(Tile, self).__init__()
        self.image = img
        self.rect = img.get_rect()
        self.rect.topleft = x, y
        # self.mask = pygame.mask.from_surface(img)
        Tile.blocks_list.add(self)

    def sprite_collide(self, _sprite, axis):
        pass

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

    def __init__(self, img, x, y):
        super(BlockingTile, self).__init__(img, x, y)
        self.friction_coeff = 0  # change to mul
        self.max_stopping_friction = float('inf')  # change if want to simulate ice or something with low friction coeff
        # self.max_stopping_friction = 0  # change if want to simulate ice or something with low friction coeff

    def sprite_collide(self, _sprite, axis):
        # if not sprite.collide_mask(self, _sprite):
        #     return
        # print(self.rect.topleft)
        if not isinstance(_sprite, AdvancedSprite):
            return
        if axis == structures.Direction.vertical:
            # print("velocity: ", _sprite.velocity.y)
            if _sprite.velocity.y > 0:  # hit from top
                # while _sprite.collide_mask(_sprite, self):
                #     _sprite.position.y -= 1
                #     _sprite.rect.y -= 1
                _sprite.rect.bottom = self.rect.top
                was_on = _sprite.on_platform
                self.friction(_sprite, was_on)
                _sprite.on_platform = self
            else:  # hit from bottom
                _sprite.rect.top = self.rect.bottom
            _sprite.position.y = _sprite.rect.y
            _sprite.force.y = 0
            _sprite.velocity.y = 0
            if hasattr(_sprite.control, 'jumping') and _sprite.control.jumping:
                _sprite.control.jumping = False
                _sprite.on_platform = None

        else:
            if _sprite.velocity.x > 0:  # hit from left
                _sprite.rect.right = self.rect.left
            else:  # hit from right
                _sprite.rect.left = self.rect.right
            _sprite.position.x = _sprite.rect.x
            _sprite.force.x = 0
            _sprite.velocity.x = 0

    def friction(self, _sprite, was_on):
        if not was_on:  # he fell on the platform
            _sprite.add_force(structures.Vector2.Cartesian(min(-_sprite.velocity.x, self.max_stopping_friction)),
                              'super friction')
        else:  # normal friction
            _sprite.add_force(structures.Vector2.Cartesian(-sign(_sprite.velocity.x) * min(self.friction_coeff,
                                                                                           abs(_sprite.velocity.x))),
                              'friction')


class Spike(BlockingTile):
    id = 2

    def sprite_collide(self, _sprite, axis):
        if isinstance(_sprite, AdvancedSprite) and _sprite.resistance_timer and axis == structures.Direction.vertical:
            _sprite.hit_points -= 1
            _sprite.resistance_timer.activate()
        super(Spike, self).sprite_collide(_sprite, axis)


class air(Tile):
    id = 3
    sur = pygame.Surface((0, 0))

    def __init__(self, x, y):
        super(air, self).__init__(air.sur, x, y)
        Tile.blocks_list.remove(self)

    def sprite_collide(self, _sprite, axis):
        pass

    def update(self):
        pass

    def draw(self):
        pass


class BaseSprite(pygame.sprite.Sprite):
    sprites_list = pygame.sprite.Group()
    image = pygame.Surface((100, 100))
    game_states = {'sprites': sprites_list, 'keys': [], 'dtime': 0}

    def __init__(self, rect, control, mass, *, rect_collision=True):
        # hit boxes & moving
        super(BaseSprite, self).__init__()
        #
        self.rect = rect
        if not hasattr(self, 'image'):
            self.image = pygame.Surface(self.rect)

        self.currently_colliding = []

        # physics
        self.position = structures.Vector2.Cartesian(*rect.topleft)
        self.velocity = structures.Vector2.Zero()
        self.acceleration = structures.Vector2.Zero()
        self.force = structures.Vector2.Zero()
        self.force_document = {}
        self.rect_collision = rect_collision
        self.mass = mass

        self.control = control

        BaseSprite.sprites_list.add(self)

    def operate_gravity(self):
        self.add_force(structures.Vector2.Cartesian(0, GRAVITY * self.mass), 'gravity', False)

    def __call__(self):
        return self.rect.center

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
        # if signature == 'gravity' and isinstance(self, Tank):
        #     print(force, signature, direction[self.control.direction])
        # if signature == 'push':
        #     print(force, signature, direction[self.control.direction])
        if mul_dtime:
            # print("Im muling with ", BaseSprite.game_states['dtime'])
            force = force / BaseSprite.game_states['dtime']
        else:
            force = force
        self.force_document[signature] = force
        self.force += force
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
        self.update(control_dict)
        self.update_kinematics(control_dict['dtime'])
        self.draw()
        self.force_document = {}

    def update(self, control_dict):
        pass

    def update_acceleration(self):
        # print(self.force)
        self.acceleration = (self.force / self.mass)  # Σ𝑓 = 𝓂 ⋅ 𝒶 -⋙ 𝒶 = Σ𝑓 / 𝓂

    def update_velocity(self, time_delta, axis=None):
        # print("on update: ", round((self.acceleration * time_delta).x, 5))
        if axis is None:
            # print("Im changin with ", time_delta)
            self.velocity += self.acceleration * time_delta
        elif axis == structures.Direction.horizontal:
            self.velocity.x += self.acceleration.x * time_delta
        elif axis == structures.Direction.vertical:
            self.velocity.y += self.acceleration.y * time_delta

    def update_position(self, axis, time_delta):
        if axis == structures.Direction.vertical:
            self.position.y += self.velocity.y * time_delta
            self.rect.y = int(self.position.y)
        else:
            self.position.x += self.velocity.x * time_delta
            self.rect.x = int(self.position.x)

    def on_platform_collision(self, direction, platform):
        """Called when the sprite collides with a platform"""
        # when finishing the game, should try to change it to forced verision
        pass

    def update_kinematics(self, time_delta):
        self.update_acceleration()
        self.update_velocity(time_delta)
        self.force.reset()

        self.update_position(structures.Direction.vertical, time_delta)

        platform = pygame_structures.Map.check_platform_collision(self, structures.Direction.vertical)
        if platform is not None:
            self.on_platform_collision(structures.Direction.vertical, platform)
            self.control.platform_collide(structures.Direction.vertical, platform)

        self.update_acceleration()
        self.update_velocity(time_delta)

        self.update_position(structures.Direction.horizontal, time_delta)
        platform = pygame_structures.Map.check_platform_collision(self, structures.Direction.horizontal)

        if platform is not None:
            self.on_platform_collision(structures.Direction.horizontal, platform)
            self.control.platform_collide(structures.Direction.horizontal, platform)

        self.force.reset()

    @classmethod
    def check_sprite_collision(cls, collision_type='mask'):
        if collision_type == 'mask':
            for idx, sprite1 in enumerate(cls.sprites_list):
                skip = idx + 1
                for sprite2 in cls.sprites_list:
                    if skip > 0:
                        skip -= 1
                        continue
                    if pygame.sprite.collide_rect(sprite1, sprite2) and pygame.sprite.collide_mask(sprite1, sprite2):

                        block_second = sprite1.collision(sprite2)
                        sprite1.control.sprite_collide(sprite2)

                        if not block_second:
                            sprite2.collision(sprite1)
                            sprite2.control.sprite_collide(sprite1)

        elif collision_type == 'rect':
            for sprite1 in cls.sprites_list:
                for sprite2 in pygame.sprite.spritecollide(sprite1, cls.sprites_list, False):
                    if sprite2 is not sprite1:
                        sprite1.collision(sprite2)
                        sprite1.control.sprite_collide(sprite2)

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
        """Called when one sprite collides with another"""
        pass


class AdvancedSprite(BaseSprite):
    """Sprite that can jump and has health bar"""
    sprites_list = pygame.sprite.Group()
    image = pygame.Surface((100, 100))

    def __init__(self, rect, control, mass, hit_points,
                 health_bar_colors: Optional[Tuple[tuple, tuple]] = None, resistance_length=0):
        # hit boxes & moving
        super(AdvancedSprite, self).__init__(rect, control, 1)
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
        self.mass = 1

        #  so the sprite will flicker when it has resistance
        self.alpha = -1
        self.delta_alpha = 1020  # brightness / second

        BaseSprite.sprites_list.add(self)

        self.platform_collide = False  # Turn on when collides with platform - vertically or horizontally -
        # used for conditions
        self.sprite_collide = False  # Turn on when collides with sprite - used for conditions

    def draw(self, draw_health=True):
        """Called on redraw function for each sprite in BaseSprite.sprites_list.
         draw the sprite to the screen"""
        if draw_health:
            if self.health_bar:
                self.health_bar.draw()

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
        self.platform_collide = False
        self.dead_check()
        self.control.move(**controls_dict)
        self.operate_gravity()
        self.update_kinematics(controls_dict['dtime'])
        self.draw()
        self.force_document = {}

    # def update_position(self, axis, time_delta):
    #     # if axis == Direction.horizontal and abs(round(self.velocity.y, 3)) != 0:
    #     #     print(self.velocity)
    #     #     self.on_platform = False
    #     super(AdvancedSprite, self).update_position(axis, time_delta)

    def update_kinematics(self, time_delta):
        self.update_acceleration()
        self.update_velocity(time_delta)
        self.force.reset()

        self.update_position(structures.Direction.vertical, time_delta)
        platform = pygame_structures.Map.check_platform_collision(self, structures.Direction.vertical)
        if platform is not None:
            self.on_platform_collision(structures.Direction.vertical, platform)
            self.control.platform_collide(structures.Direction.vertical, platform)
            self.platform_collide = platform

        self.on_platform = platform

        self.update_acceleration()
        self.update_velocity(time_delta)

        self.update_position(structures.Direction.horizontal, time_delta)
        platform = pygame_structures.Map.check_platform_collision(self, structures.Direction.horizontal)

        if platform is not None:
            self.on_platform_collision(structures.Direction.horizontal, platform)
            self.control.platform_collide(structures.Direction.horizontal, platform)
            self.control.platform_collide(structures.Direction.vertical, platform)
            self.platform_collide = platform

        self.force.reset()

    def collision(self, other):
        self.sprite_collide = other

    def dead_check(self):
        if self.hit_points <= 0 and not self.is_dead:
            self.is_dead = True
            return True
            # recommended to add a death sound
        return False


class DrivableSprite(AdvancedSprite):
    def __init__(self, rect, control, mass, hit_points,
                 health_bar_colors: Optional[Tuple[tuple, tuple]] = None, resistance_length=0):
        super(DrivableSprite, self).__init__(rect, control, mass, hit_points, health_bar_colors, resistance_length)
        self.vehicle = None

    def _update(self, controls_dict):
        if self.vehicle is None:
            super(DrivableSprite, self).__update(controls_dict)
        else:
            self.rect.topleft = self.vehicle.get_sprite_position()  # update position to vehicle position
            self.position.values = self.rect.topleft

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
        super(Bullet, self).__init__(rect, controls.NoMoveControl(self, None), 1)
        self.damage = damage
        self.travel_distance = travel_distance
        self.first_frame = True

    def __str__(self):
        return super(Bullet, self).__str__() + f', travel_distance{self.travel_distance}'

    def update_position(self, axis, time_delta):
        if axis == structures.Direction.vertical:
            if self.travel_distance <= 0:
                self.kill()
            self.travel_distance -= abs(self.velocity.x * time_delta)
        super(Bullet, self).update_position(axis, time_delta)

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

    def on_platform_collision(self, direction, platform):
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


def tick(elapsed, clock, keys=pygame.key.get_pressed()):
    # print(len(BaseSprite.sprites_list))
    start = time()
    BaseSprite.update_states(keys, elapsed)
    pygame_structures.Camera.reset_frame()
    # BaseSprite.check_sprite_collision()
    Particles.Particle.check_all_collision(BaseSprite.sprites_list)
    BaseSprite.update_all()
    BaseSprite.check_sprite_collision()
    Particles.Particle.update_all()
    Tile.update_all()
    pygame_structures.Camera.scroller.update()
    structures.UntilCondition.update_all()
    # Timer.tick_all(clock.get_fps())

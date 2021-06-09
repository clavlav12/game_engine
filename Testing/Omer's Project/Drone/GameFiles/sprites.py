from Engine.Debug import *
from Engine import base_sprites
from Engine import base_control
from Engine.structures import Vector2, Direction
from enum import Enum
import pygame as pg
import random


class Color(Enum):
    black = 0
    blue = 1


# colors = vars(Color)
# print(colors)

class BetterAllDirectionMovement(base_control.BaseControl):
    MOVING_SPEED = 350  # p/s
    DIRECTION_TO_VECTOR = {
        Direction.left: Vector2.Cartesian(-1),
        Direction.right: Vector2.Cartesian(1),
        Direction.up: Vector2.Cartesian(y=-1),
        Direction.down: Vector2.Cartesian(y=1)
    }

    def __init__(self, sprite, key_up=pg.K_UP,
                 key_down=pg.K_DOWN,
                 key_left=pg.K_LEFT,
                 key_right=pg.K_RIGHT,
                 moving_speed=MOVING_SPEED,
                 default_direction=Direction.left):
        super(BetterAllDirectionMovement, self).__init__(sprite, default_direction)

        self.speed = moving_speed
        self.moving_direction = self.DIRECTION_TO_VECTOR[self.direction]
        self.key_left = key_left
        self.key_right = key_right
        self.key_down = key_down
        self.key_up = key_up

    def reset(self):
        base_control.BaseControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        pressed_keys = kwargs['keys']
        self.moving_direction = Vector2.Zero()
        if pressed_keys[self.key_right]:  # moving right
            self.moving_direction += self.DIRECTION_TO_VECTOR[Direction.right]
        if pressed_keys[self.key_left]:  # moving left
            self.moving_direction += self.DIRECTION_TO_VECTOR[Direction.left]

        if not self.moving_direction.x:
            self.stop(Direction.horizontal)

        if pressed_keys[self.key_up]:
            self.moving_direction += self.DIRECTION_TO_VECTOR[Direction.up]
        elif pressed_keys[self.key_down]:
            self.moving_direction += self.DIRECTION_TO_VECTOR[Direction.down]

        if not self.moving_direction.y:
            self.stop(Direction.horizontal)

        self.moving_direction.normalize()

        self.sprite.add_force(
            self.moving_direction * self.speed * self.sprite.mass
        )

    def stop(self, direction):
        unit = self.DIRECTION_TO_VECTOR[direction]
        self.sprite.add_force(- unit * unit * self.sprite.velocity, 'stop movement')


class Drone(base_sprites.BaseSprite):
    blue = pg.image.load('Arts/drone_grey.png')
    black = pg.image.load('Arts/drone_black.png')
    gold = pg.image.load('Arts/drone_gold.png')

    size = 50
    blue = pg.transform.scale(blue, (size, size))
    black = pg.transform.scale(black, (size, size))
    gold = pg.transform.scale(gold, (size, size))

    def __init__(self, x, y, controls, color: Color):
        super(Drone, self).__init__(
            pg.Rect(x, y, self.size, self.size),
            base_control.BetterAllDirectionMovement(self, *controls[:-2]),
            50,
        )

        self.golden = False
        self.controls = controls
        self.color = color

        self.image = {
            0: self.black,
            1: self.blue
        }[color.value]

    def make_gold(self):
        if self.golden:
            return

        self.golden = True
        self.image = self.gold

    def collision(self, other):
        if not isinstance(other, Drone):
            return

        if self.golden:
            self.kill()
            self.generate_drone(self.controls, self.color)

    @classmethod
    def generate_drone(cls, controls, color):
        W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

        return Drone(
            random.randint(0, W - cls.size),
            random.randint(0, H - cls.size),
            controls,
            color
        )


# class GoldenPool(base_sprites.BaseSprite):
#     def __init__(self, x, y, w, h):
#         super(GoldenPool, self).__init__(
#             pg.Rect(x, y, w, h),
#             base_control.NoMoveControl(),
#             500
#         )
#
#         self.image = pg.Surface((w, h), pg.SRCALPHA)
#         self.image.fill(pg.Color('gold'))
#
#     def collision(self, other, collision):
#         if isinstance(other, Drone):
#             other.make_gold()
#
#     @classmethod
#     def generate_pool(cls):
#         W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height
#
#         pool_size = (200, 200)
#
#         return GoldenPool(
#             random.randint(0, W - pool_size[0]),
#             random.randint(0, H - pool_size[1]),
#             *pool_size
#         )

    # def draw(self):


class WinningTile(base_sprites.BlockingTile):
    game_ended = False
    id = 5

    def __init__(self, *, x, y, group):
        ts = pygame_structures.Map.instance.tile_size
        ts = (ts, ts)
        image = pg.Surface(ts, pg.SRCALPHA)
        image.fill(pg.Color('green'))
        super(WinningTile, self).__init__(
            image, group, 0, 0, 0, x=x, y=y
        )

    def sprite_collide(self, _sprite, collision):
        if isinstance(_sprite, Drone) and _sprite.golden:
            color = _sprite.color
            pygame_structures.Camera.display_text(f'{color.name} Wins!!', 'center', 'Winning')
            WinningTile.game_ended = True

        super(WinningTile, self).sprite_collide(_sprite, collision)


class GoldenPool(base_sprites.BlockingTile):
    id = 6

    def __init__(self, *, x, y, group):
        ts = pygame_structures.Map.instance.tile_size
        ts = (ts, ts)
        image = pg.Surface(ts, pg.SRCALPHA)
        image.fill(pg.Color('gold'))
        super(GoldenPool, self).__init__(
            image, group, 0, 0, 0, x=x, y=y
        )

    def sprite_collide(self, _sprite, collision):
        if isinstance(_sprite, Drone):
            _sprite.make_gold()

        super(GoldenPool, self).sprite_collide(_sprite, collision)



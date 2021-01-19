from Engine import pygame_structures
from Engine.Debug import *
from Engine import base_sprites
from Engine import base_control
from Engine import structures
from Engine import Geometry
from typing import Union, Tuple, List
from collections import namedtuple
from enum import Enum
import Bodies
import pygame as pg
import random
import math
import os


class Color(Enum):
    black = 0
    blue = 1


# colors = vars(Color)
# print(colors)


class Drone(base_sprites.BaseSprite):
    blue = pg.image.load('Omer')
    black = pg.image.load('Omer')
    gold = pg.image.load('Omer')

    size = 50
    blue = pg.transform.scale(blue, (size, size))
    black = pg.transform.scale(black, (size, size))
    gold = pg.transform.scale(gold, (size, size))

    def __init__(self, x, y, controls, color: Color):
        super(Drone, self).__init__(
            pg.Rect(x, y, self.size, self.size),
            base_control.AllDirectionMovement(self, *controls[:-2]),
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

    def collision(self, other, collision):
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
            image, 0, 0, 0, x=x, y=y, group=group
        )


    def sprite_collide(self, _sprite, collision: pygame_structures.collision_manifold):
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
            image, 0, 0, 0, x=x, y=y, group=group
        )

    def sprite_collide(self, _sprite, collision: pygame_structures.collision_manifold):
        if isinstance(_sprite, Drone):
            _sprite.make_gold()

        super(GoldenPool, self).sprite_collide(_sprite, collision)



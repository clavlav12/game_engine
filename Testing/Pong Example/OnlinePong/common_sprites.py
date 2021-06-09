from Engine.base_sprites import BaseSprite, basic_loop
from Engine.base_control import UpDownMovement, BaseControl
from Engine import pygame_structures
import pygame as pg
from time import time


class Ball(BaseSprite):
    R = 10
    K = R * 2
    COLOR = pg.Color('white')
    SPEED = 400
    # SPEED = 800

    def __init__(self, position, angle):
        super(Ball, self).__init__(
            rect=pg.Rect(position[0] - self.R, position[1] - self.R, self.K, self.K),
            control=None,
            manifold_generator=BaseSprite.basic_generator,
            mass=1,
            sprite_collision_by_rect=True
        )
        self.restitution = 1
        self.image = pg.Surface((self.K, self.K), pg.SRCALPHA)
        pg.draw.circle(self.image, self.COLOR, (self.R, self.R), self.R)
        self.s = time()
        self.angle = 0
        self.static_friction = 0
        self.dynamic_friction = 0.09

    def solved_collision(self, other):
        self.velocity.r = self.SPEED

    @classmethod
    def encode_creation(cls, **kwargs):
        position = kwargs['position']
        return {
            'x': position[0],
            'y': position[1],
            'angle': kwargs['angle']
        }

    @classmethod
    def decode_creation(cls, **kwargs):
        return {
            'position': (int(kwargs['x']), int(kwargs['y'])),
            'angle': int(kwargs['angle'])
        }

    def update(self, _):
        if time() - self.s > 10:
            self.velocity.r = self.SPEED
            self.velocity.theta = self.angle
            self.s = float('inf')


class BatControl(BaseControl, UpDownMovement):
    SPEED = 250
    SPEED = 500

    def __init__(self, sprite, up_key, down_key):
        BaseControl.__init__(self, sprite)
        UpDownMovement.__init__(self, self.SPEED, sprite)
        self.up_key = up_key
        self.down_key = down_key

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        keys = kwargs['keys']
        if keys[self.up_key]:
            self.move_up()
        elif keys[self.down_key]:
            self.move_down()
        else:
            self.stop()


class Bat(BaseSprite):
    WIDTH = 20
    HEIGHT = 140
    COLOR = pg.Color('white')

    def __init__(self, position):
        super(Bat, self).__init__(
            rect=pg.Rect(position[0] - self.WIDTH // 2, position[1] - self.HEIGHT // 2, self.WIDTH, self.HEIGHT),
            control=BatControl(self, pg.K_UP, pg.K_DOWN),
            mass=9.e10,
            tile_collision_by_rect=True
        )
        self.static_friction = 0
        self.dynamic_friction = 0.05
        self.restitution = 1

        self.image = pg.Surface((self.WIDTH, self.HEIGHT))
        self.image.fill(self.COLOR)

    @classmethod
    def encode_creation(cls, **kwargs):
        position = kwargs['position']
        return {
            'x': position[0],
            'y': position[1],
        }

    @classmethod
    def decode_creation(cls, **kwargs):
        return {
            'position': (int(kwargs['x']), int(kwargs['y'])),
        }


W, H = 500, 500


def make_map():
    tile_size = [max(W, H)] * 2
    sur = pg.Surface(tile_size)
    sur.fill((0, 0, 255))

    first = [
        [{'id': 3} for _ in range(50)] for __ in range(50)
    ]
    first[1][0] = {'id': 1, 'img': sur, 'group': None}
    forth = [
        [{'id': 3} for _ in range(50)] for __ in range(50)
    ]
    forth[-2][0] = {'id': 1, 'img': sur, 'group': None}
    # pygame_structures.Map(first, [], [], [], 25)
    pygame_structures.Map(first, [], [], forth, tile_size[0])


# make_map()
#
# pygame_structures.Camera.init(screen, "dynamic", None)
#
# OFFSET = 50
# left_bat = Bat(pg.K_w, pg.K_s, (OFFSET, H // 2))
# right_bat = Bat(pg.K_UP, pg.K_DOWN, (W - OFFSET, H // 2))
#
# ball = Ball((W // 2, H // 2 - 150), 0)
# pygame_structures.Camera.add_blit_order(
#     lambda scrn: pg.draw.line(scrn, Bat.COLOR, (W//2, H) - pygame_structures.Camera.scroller,
#                               (W//2, 0) - pygame_structures.Camera.scroller), float('inf'))
#
# pygame_structures.Camera.set_scroller_position(ball)
# basic_loop()
#

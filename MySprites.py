from glob import glob as files_in_dir
import controls_new as controls
# import controls
import Sound
from structures import *
import pygame
from GlobalUse import meters, pixels, meters_multi, DisplayMods
from typing import Tuple, Optional
import os
from pymaybe import maybe
from numpy import sign
from collections import namedtuple
from itertools import repeat

pygame.init()
player = Sound.Player()
clock = pygame.time.Clock()
GRAVITY = 3_000


# GRAVITY = 30


def smooth_scale_image(img, scale):
    return pygame.transform.smoothscale(img, mul_tuple(img.get_size(), scale)).convert_alpha()


def smooth_scale_images(lst, scale):
    return [smooth_scale_image(i, scale) for i in lst]


def get_images_list(path, scale=None, crop_rect=None, sort_key=None):
    if sort_key:
        files = sorted(files_in_dir(path), key=sort_key)
    else:
        files = files_in_dir(path)
    lst = []
    for file in files:
        img = pygame.image.load(file).convert_alpha()
        wid = img.get_width()
        hei = img.get_height()
        if scale is not None and scale != 1:
            img = pygame.transform.smoothscale(img, (int(wid * scale), int(hei * scale))).convert_alpha()
        if crop_rect:
            img = img.subsurface((crop_rect.x, crop_rect.y, img.get_width - crop_rect.width, img.get_height -
                                  crop_rect.height))
        lst.append(img)
    return lst


def singleton_classmethod(function):
    def inner(*args, **kwargs):
        assert Map.instance is not None, "No Map"
        if args and isinstance(args[0], Map):
            return function(*args, **kwargs)
        else:
            return function(Map.instance, *args, **kwargs)

    return inner


class Map:
    instance = None

    def __init__(self, first_quadrant,
                 second_quadrant,
                 third_quadrant,
                 forth_quadrant,
                 tile_size):
        assert Map.instance is None, "Two Maps?!"
        """
        :param mp: 2 dimensional list
        """
        self.first_quadrant = [[Tile.get_tile(tile_id)(*args, x * tile_size, y * tile_size)
                                for x, (tile_id, *args) in enumerate(row)] for y, row in enumerate(first_quadrant)]

        self.second_quadrant = [[Tile.get_tile(tile_id)(*args, -x * tile_size, y * tile_size)
                                 for x, (tile_id, *args) in enumerate(reversed(row))]
                                for y, row in enumerate(second_quadrant)]
        self.third_quadrant = [[Tile.get_tile(tile_id)(*args, -x * tile_size, -y * tile_size)
                                for x, (tile_id, *args) in enumerate(reversed(row))]
                               for y, row in enumerate(reversed(third_quadrant))]
        self.forth_quadrant = [[Tile.get_tile(tile_id)(*args, x * tile_size, -y * tile_size)
                                for x, (tile_id, *args) in enumerate(row)] for y, row in
                               enumerate(reversed(forth_quadrant))]

        # print(*[['0' if isinstance(tile, air) else '1' for tile in column] for column in self.map], sep='\n')
        self.map_maps = {
            (1, 1): self.first_quadrant,
            (-1, 1): self.second_quadrant,
            (-1, -1): self.third_quadrant,
            (1, -1): self.forth_quadrant,

        }
        self.tile_size = tile_size
        Map.instance = self

    def get_tile(self, x, y):
        return self.map_maps[(int(math.copysign(1, x)), int(math.copysign(1, y)))][abs(y)][abs(x)]

    @classmethod
    def from_file(cls, file):
        pass

    @singleton_classmethod
    def get_map(self, x, y):
        return self.map_maps[(int(math.copysign(1, x)), int(math.copysign(1, y)))]

    @singleton_classmethod
    def check_platform_collision(self, sprite, axis):
        x, y, width, height = sprite.position.x, sprite.position.y, sprite.rect.width, sprite.rect.height
        left = int(x // self.tile_size)
        right = int((x + width) // self.tile_size)
        top = int(y // self.tile_size)
        bottom = int((y + height) // self.tile_size)

        # print((left, top), (right, bottom))
        if (y + height) / self.tile_size == bottom:
            bottom -= 1
        if y / self.tile_size == top:
            top += 1
        if x / self.tile_size == left:
            left += 1
        if (x + width) / self.tile_size == right:
            right -= 1

        row, column = 0, 0
        for column in range(top, bottom + 1):
            for row in range(left, right + 1):
                try:
                    tile = self.get_tile(row, column)
                    if not isinstance(tile, air):
                        if sprite.rect_collision or \
                                pygame.sprite.collide_mask(tile, sprite):  # mask
                            tile.sprite_collide(sprite, axis)
                            return tile

                except IndexError:  # no collision
                    pass

        return None


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
        Camera.blit(self.image, self.rect.topleft - Camera.scroller)

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
        if axis == Direction.vertical:
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
            _sprite.add_force(Vector2.Cartesian(min(-_sprite.velocity.x, self.max_stopping_friction)), 'super friction')
        else:  # normal friction
            _sprite.add_force(Vector2.Cartesian(-sign(_sprite.velocity.x) * min(self.friction_coeff,
                                                                                abs(_sprite.velocity.x))), 'friction')


class Spike(BlockingTile):
    id = 2

    def sprite_collide(self, _sprite, axis):
        if isinstance(_sprite, AdvancedSprite) and _sprite.resistance_timer and axis == Direction.vertical:
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


class Camera:
    """Static class to handle scroller out of this file"""
    fnt = pygame.font.SysFont('comicsansms', 45)
    Text = namedtuple('Text', ['text', 'position', 'signature'])
    displayed_text = []  # Text(text, position, signature)
    scroller = None
    screen = None
    real_screen = None
    shake_offset = repeat((0, 0))
    background = (20, 24, 82)
    save = False
    display_fps = True
    fps_font = pygame.font.SysFont('comicsansms', 12)

    @classmethod
    def init(cls, display_mode, scroller_type='static', scroller_edges=None,
             scroller__starting_position=None):

        if scroller_type == 'static':
            cls.scroller = Scroller(lambda: (pygame.display.Info().current_h, pygame.display.Info().current_w),
                                    DisplayMods.get_resolution(), starting_position=scroller__starting_position,
                                    minx=0, maxx=0,
                                    miny=0, maxy=0)
        elif scroller_type == 'dynamic':
            cls.scroller = Scroller(lambda: (pygame.display.Info().current_w / 2, pygame.display.Info().current_h / 2),
                                    DisplayMods.get_resolution(), starting_position=scroller__starting_position, )
        elif scroller_type == 'half dynamic':
            maxx, minx, maxy, miny = scroller_edges
            cls.scroller = Scroller(lambda: (pygame.display.Info().current_h, pygame.display.Info().current_w),
                                    DisplayMods.get_resolution(), starting_position=scroller__starting_position,
                                    minx=minx, maxx=maxx,
                                    miny=miny, maxy=maxy)
        else:
            raise AttributeError("invalid scroller type")

        cls.real_screen = display_mode
        cls.screen = cls.real_screen.copy()

    @classmethod
    def set_scroller_position(cls, position, smooth_move=False):
        cls.scroller.set_position(position, smooth_move)

    @classmethod
    def get_scroller(cls):
        return cls.scroller

    @staticmethod
    def add_particle(particle, *args, **kwargs):
        particle(*args, **kwargs)

    @classmethod
    def display_text(cls, font, text: str, position, signature):
        sur = font.render(text)
        if position == 'center':
            r = sur.get_rect(center=mul_tuple(cls.screen.get_size(), 0.5))
            position = r.topleftdw
        cls.displayed_text.append(cls.Text(sur, position, signature))

    @classmethod
    def remove_text(cls, signature):
        for txt in cls.displayed_text:
            if txt.signature == signature:
                break
        else:  # if not break
            raise AttributeError(f"Signature {signature} not found")
        cls.displayed_text.remove(txt)

    @classmethod
    def shake(cls):
        cls.shake_offset = cls.shake_generator()

    @staticmethod
    def shake_generator():
        """this function creates our shake-generator
        it "moves" the screen to the left and right
        three times by yielding (-5, 0), (-10, 0),
        ... (-20, 0), (-15, 0) ... (20, 0) three times,
        then keeps yielding (0, 0) until next time called"""

        s = -1
        for _ in range(0, 8):
            for x in range(0, 20, 5):
                yield (x * s, 0)
            for x in range(20, 0, 5):
                yield (x * s, 0)
            s *= -1
        while True:
            yield (0, 0)

    @classmethod
    def blit(cls, surface, position):
        cls.screen.blit(surface, position)

    @classmethod
    def post_process(cls):
        for txt in cls.displayed_text:
            cls.blit(txt.text, txt.position)
        if cls.display_fps:
            fps_surface = cls.fps_font.render(str(round(clock.get_fps())) + ', ' + str(len(BaseSprite.sprites_list)),
                                              True, pygame.Color('white'))
            cls.blit(fps_surface, (5, 5))
        cls.real_screen.blit(cls.screen, next(cls.shake_offset))
        if cls.save:
            pygame.image.save(cls.screen, 'saved.png')
            quit()

    @classmethod
    def reset_frame(cls):
        cls.screen.fill(cls.background)


movement_status = {
    0: 'idle',
    1: 'starting',
    2: 'moving',
    3: 'stopping'}


class HealthBar:
    HEIGHT_CONST = 0.2

    def __init__(self, pos_color, neg_color, advanced_sprite):
        self.sprite = advanced_sprite
        self.neg_color = neg_color
        self.pos_color = pos_color

        self.bar_height = round(self.sprite.rect.height * HealthBar.HEIGHT_CONST)
        bar_width = self.sprite.rect.width
        self.negative_bar_rect = pygame.Rect(self.sprite.rect.x, self.sprite.rect.y - self.bar_height, bar_width,
                                             self.bar_height)
        self.positive_bar_rect = pygame.Rect(self.sprite.rect.x, self.sprite.rect.y - self.bar_height, bar_width *
                                             (self.sprite.base_hit_points // self.sprite.hit_points), self.bar_height)

    def draw(self):
        bar_width = self.sprite.rect.width
        self.negative_bar_rect.x = self.sprite.rect.x - Camera.scroller['x']
        self.negative_bar_rect.y = self.sprite.rect.y - self.bar_height - Camera.scroller['y']
        self.positive_bar_rect.x = self.sprite.rect.x - Camera.scroller['x']
        self.positive_bar_rect.y = self.sprite.rect.y - self.bar_height - Camera.scroller['y']

        self.positive_bar_rect.width = max(round(bar_width * (self.sprite.hit_points / self.sprite.base_hit_points)), 0)

        pygame.draw.rect(Camera.screen, self.neg_color, self.negative_bar_rect)
        if not self.positive_bar_rect.width == 0:
            pygame.draw.rect(Camera.screen, self.pos_color, self.positive_bar_rect)


'''
class oldAnimation:
    """Collection class to make animations easier"""
    _key = object()

    def __init__(self, creation_key, parameter, fpi, repeat, flip_x, flip_y, scale):
        if creation_key is not Animation._key:
            raise PrivateConstructorAccess(f"Access denied to private constructor of class {Animation}")
        if isinstance(parameter, str):
            self.images_list = [pygame.transform.flip(pygame.image.load(i), flip_x, flip_y) for i in
                                files_in_dir(parameter)]
        elif isinstance(parameter, list):
            if flip_x or flip_y:
                self.images_list = [pygame.transform.flip(pygame.image.load(i).convert_alpha(), flip_x, flip_y) for i in
                                    parameter]
            else:
                self.images_list = parameter
        if scale != 1:
            self.images_list = [pygame.transform.smoothscale(i, (int(i.get_width() * scale),
                                                                 int(i.get_height() * scale))) for i in
                                self.images_list]
        self.convert_alpha()
        assert bool(self.images_list), "image list is empty"
        self.pointer = 0
        self.frames_per_image = fpi
        self.repeat = repeat

    def convert_alpha(self):
        self.images_list = [i.convert_alpha() for i in self.images_list]

    @classmethod
    def by_images_list(cls, lst, frames_per_image=1, repeat=True, flip_x=False, flip_y=False, scale=1):
        """
        :param lst:  list of surfaces (list)
        :param frames_per_image:  frames until image switches (int)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        """
        return cls(cls._key, lst, frames_per_image, repeat, flip_x, flip_y, scale)

    @classmethod
    def by_directory(cls, dir_regex, frames_per_image=1, repeat=True, flip_x=False, flip_y=False, scale=1):
        """
        :param dir_regex:  directory path regex (string)
        :param frames_per_image:  frames until image switches (int)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        :return: Animation object (Animation)
        """
        return cls(cls._key, dir_regex, frames_per_image, repeat, flip_x, flip_y, scale)

    def get_image(self, count_pointer=True):
        pointer_pos = self.pointer
        if count_pointer:
            can_add = self.update_pointer()
            if can_add:
                pointer_pos -= 1
        return self.images_list[int(pointer_pos // self.frames_per_image)]

    def update_pointer(self):
        self.pointer += 1
        if self.pointer > self.frames_per_image * len(self.images_list):
            if self.repeat:
                self.pointer = 0
            else:
                self.pointer -= 1
            return True
        return False

    def reset(self):
        self.pointer = 0

    def finished(self):
        return (not self.repeat) and self.pointer == len(self.images_list) * self.frames_per_image

    def __next__(self):
        return self.get_image()

    def get_next_size(self):
        # Returns the size of the next image
        return self.images_list[int(self.pointer // self.frames_per_image)].get_size()

    def __len__(self):
        return len(self.images_list)
'''


class Animation:
    """Collection class to make animations easier"""
    _key = object()

    def __init__(self, creation_key, parameter, fps, repeat, flip_x, flip_y, scale):
        if creation_key is not Animation._key:
            raise PrivateConstructorAccess(f"Access denied to private constructor of class {Animation}")
        if isinstance(parameter, str):
            self.images_list = [pygame.transform.flip(pygame.image.load(i), flip_x, flip_y) for i in
                                files_in_dir(parameter)]
        elif isinstance(parameter, list):
            if flip_x or flip_y:
                self.images_list = [pygame.transform.flip(pygame.image.load(i).convert_alpha(), flip_x, flip_y) for i in
                                    parameter]
            else:
                self.images_list = parameter
        if scale != 1:
            self.images_list = [pygame.transform.smoothscale(i, (int(i.get_width() * scale),
                                                                 int(i.get_height() * scale))) for i in
                                self.images_list]
        self.convert_alpha()
        assert bool(self.images_list), "image list is empty"
        self.pointer = 0
        self.frames_per_second = fps
        self.timer = Timer(1 / self.frames_per_second)
        self.repeat = repeat

    def convert_alpha(self):
        self.images_list = [i.convert_alpha() for i in self.images_list]

    @classmethod
    def by_images_list(cls, lst, frames_per_image=1, repeat=True, flip_x=False, flip_y=False, scale=1):
        """
        :param lst:  list of surfaces (list)
        :param frames_per_image:  frames until image switches (int)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        """
        return cls(cls._key, lst, frames_per_image, repeat, flip_x, flip_y, scale)

    @classmethod
    def by_directory(cls, dir_regex, frames_per_image=1, repeat=True, flip_x=False, flip_y=False, scale=1):
        """
        :param dir_regex:  directory path regex (string)
        :param frames_per_image:  frames until image switches (int)
        :param repeat: after finished to show all images, whether reset pointer or not (bool)
        :param flip_x: should the image be flipped horizontally (bool)
        :param flip_y: should the image be flipped vertically (bool)
        :param scale: how much to scale the image (int)
        :return: Animation object (Animation)
        """
        return cls(cls._key, dir_regex, frames_per_image, repeat, flip_x, flip_y, scale)

    def get_image(self):
        if not self.timer.is_counting:
            if self.timer.finished():
                self.update_pointer()
                self.timer.activate()
        return self.images_list[self.pointer]  # ??

    def update_pointer(self):
        self.pointer += 1
        if self.pointer >= len(self.images_list):  # ??
            if self.repeat:
                self.pointer = 0
            else:
                self.pointer -= 1
            return True
        return False

    def reset(self):
        self.pointer = 0

    def finished(self):
        return (not self.repeat) and self.pointer == len(self.images_list) - 1  # ??

    def __next__(self):
        return self.get_image()

    def get_next_size(self):
        # Returns the size of the next image
        return self.images_list[self.pointer].get_size()

    def __len__(self):
        return len(self.images_list)

'''
class Timer:
    """Used to time stuff eg. jump, fire etc."""
    timers_list = []

    def __init__(self, delay, active=False):
        self.delay = delay
        self.base_delay = delay
        self.timer = 0.0
        self.is_counting = False
        Timer.timers_list.append(self)
        if active:
            self.activate()
            self.timer = 1.e-5

    def tick(self, fps):
        if self.is_counting:
            try:
                self.timer += 1 / fps
            except ZeroDivisionError:
                self.timer += 1.e-5
            if self.timer >= self.delay:
                self.is_counting = False
                self.timer = 0
                return True
        return False

    def reset(self):
        self.timer = 0

    def activate(self, t=None):
        if t:
            self.delay = t
        else:
            self.delay = self.base_delay
        self.is_counting = True

    def __bool__(self):
        return self.timer == 0

    def finished(self):
        return bool(self)

    @classmethod
    def tick_all(cls, fps):
        for timer in cls.timers_list:
            if timer.is_counting:
                timer.tick(fps)
'''

class Timer:
    """Used to time stuff eg. jump, fire etc."""

    def __init__(self, delay, active=False):
        self.delay = delay
        self.base_delay = delay
        self._is_counting = False
        self.start_time = -1
        if active:
            self.activate()

    @property
    def is_counting(self):
        if self.finished() and self._is_counting:
            self._is_counting = False
        return self._is_counting

    def reset(self):
        self.start_time = time()

    def activate(self, new_time=None):
        if new_time:
            self.delay = new_time
        else:
            self.delay = self.base_delay
        self.start_time = time()
        self._is_counting = True

    def __bool__(self):
        return self.delay < (time() - self.start_time)

    def finished(self):
        return bool(self)


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
        self.position = Vector2.Cartesian(*rect.topleft)
        self.velocity = Vector2.Zero()
        self.acceleration = Vector2.Zero()
        self.force = Vector2.Zero()
        self.force_document = {}
        self.rect_collision = rect_collision
        self.mass = mass

        self.control = control

        BaseSprite.sprites_list.add(self)

    def operate_gravity(self):
        self.add_force(Vector2.Cartesian(0, GRAVITY * self.mass), 'gravity', False)

    def __call__(self):
        return self.rect.center

    def draw_rect(self, clr=pygame.Color('red')):
        r = pygame.Rect(self.rect)
        r.topleft = r.topleft - Camera.scroller
        pygame.draw.rect(Camera.screen, clr, r, 1)

    def add_force(self, force: Vector2, signature=None, mul_dtime=True):
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
        Camera.blit(self.image, self.rect.topleft - Camera.scroller)

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
        elif axis == Direction.horizontal:
            self.velocity.x += self.acceleration.x * time_delta
        elif axis == Direction.vertical:
            self.velocity.y += self.acceleration.y * time_delta

    def update_position(self, axis, time_delta):
        if axis == Direction.vertical:
            self.position.y += self.velocity.y * time_delta
            self.rect.y = int(self.position.y)
        else:
            self.position.x += self.velocity.x * time_delta
            self.rect.x = int(self.position.x)

    def check_platform_collision(self, axis):
        # platforms = filter(lambda plat: sprite.collide_mask(self, plat),
        #                    pygame.sprite.spritecollide(self, Block.blocks_list, False))
        # platforms1 = pygame.sprite.spritecollide(self, Block.blocks_list, False)
        platforms = filter(lambda block: accurate_rect_collide(self.rect, block.rect,
                                                               (math.modf(self.position.x)[0],
                                                                math.modf(self.position.y)[0])), Tile.blocks_list)

        platform = None
        for platform in platforms:
            platform.sprite_collide(self, axis)

        return platform

    def on_platform_collision(self, direction, platform):
        """Called when the sprite collides with a platform"""
        # when finishing the game, should try to change it to forced verision
        pass

    def update_kinematics(self, time_delta):
        self.update_acceleration()
        self.update_velocity(time_delta)
        self.force.reset()

        self.update_position(Direction.vertical, time_delta)

        platform = Map.check_platform_collision(self, Direction.vertical)
        if platform is not None:
            self.on_platform_collision(Direction.vertical, platform)
            self.control.platform_collide(Direction.vertical, platform)

        self.update_acceleration()
        self.update_velocity(time_delta)

        self.update_position(Direction.horizontal, time_delta)
        platform = Map.check_platform_collision(self, Direction.horizontal)

        if platform is not None:
            self.on_platform_collision(Direction.horizontal, platform)
            self.control.platform_collide(Direction.horizontal, platform)

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
        self.resistance_timer = Timer(resistance_length)
        self.is_dead = False
        self.visible = True

        if health_bar_colors is not None:
            self.health_bar = HealthBar(*health_bar_colors, self)
        else:
            self.health_bar = None
        # self.stand_on_platform = False
        self.on_platform = False
        # physics
        self.velocity = Vector2.Zero()
        self.acceleration = Vector2.Zero()
        self.force = Vector2.Zero()
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

        self.update_position(Direction.vertical, time_delta)
        platform = Map.check_platform_collision(self, Direction.vertical)
        if platform is not None:
            self.on_platform_collision(Direction.vertical, platform)
            self.control.platform_collide(Direction.vertical, platform)
            self.platform_collide = platform

        self.on_platform = platform

        self.update_acceleration()
        self.update_velocity(time_delta)

        self.update_position(Direction.horizontal, time_delta)
        platform = Map.check_platform_collision(self, Direction.horizontal)

        if platform is not None:
            self.on_platform_collision(Direction.horizontal, platform)
            self.control.platform_collide(Direction.horizontal, platform)
            self.control.platform_collide(Direction.vertical, platform)
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


class Tank(Vehicle):
    scale = 0.5
    position_offset = (85 * scale, 98 * scale)
    pivot_offset = (-20 * scale, 0)
    TURRET_IMAGE = pygame.transform.flip(pygame.image.load('images/main-turret.png'), True, False).convert_alpha()
    TURRET_IMAGE = smooth_scale_image(TURRET_IMAGE, scale)

    MOVE_LEFT_IMAGES = get_images_list(r'animation\tank' + '\\[1-9]*.png', scale)
    smooth_scale_images(MOVE_LEFT_IMAGES, scale)
    MOVE_RIGHT_IMAGES = [pygame.transform.flip(x, True, False).convert_alpha() for x in MOVE_LEFT_IMAGES]
    HIT_POINTS = 2000

    def __init__(self, init_direction, position, left_key=pygame.K_LEFT, right_key=pygame.K_RIGHT,
                 shoot_key=pygame.K_SPACE,
                 turret_up_key=pygame.K_UP, turret_down_key=pygame.K_DOWN, health_bar_color=None):
        self.moving_left_animation = Animation.by_images_list(Tank.MOVE_LEFT_IMAGES, 10)
        self.moving_right_animation = Animation.by_images_list(Tank.MOVE_RIGHT_IMAGES, 10)
        if init_direction == Direction.right:
            self.image = self.moving_right_animation.get_image()
        elif init_direction == Direction.left:
            self.image = self.moving_left_animation.get_image()
        super(Tank, self).__init__(self.image.get_rect(),
                                   controls.TankControl(left_key, right_key, shoot_key, turret_up_key, turret_down_key
                                                        , self, init_direction),
                                   1, (0, 0), Tank.HIT_POINTS, health_bar_color)
        self.rect.topleft = position
        self.position.values = self.rect.topleft
        self.turret_angle = 0
        self.turret_image = FlippableRotatedImage(Tank.TURRET_IMAGE, self.turret_angle, Tank.pivot_offset,
                                                  Tank.position_offset,
                                                  self.rect, Direction.left)

    def set_turret_angle(self, angle):
        self.turret_angle = max(min((abs(angle) % 380) * sign(angle), 116), -45)
        self.turret_image.rotate(self.turret_angle)

    def change_turret_angle(self, angle_change):
        self.set_turret_angle(self.turret_angle + angle_change)

    def draw(self):
        if self.hit_points > 0:
            self.turret_image.blit_image(self.control.direction)
            if self.control.direction == Direction.right:
                self.image = self.moving_right_animation.get_image()
            elif self.control.direction == Direction.left:
                self.image = self.moving_left_animation.get_image()
            super(Tank, self).draw()

        # self.draw_rect()


class RotatableImage:
    def __init__(self, img: pygame.Surface, init_angle, center_offset, position: callable):
        if callable(position):
            self.position = position  # center position
        elif isinstance(position, tuple):
            if len(position) == 2:
                self.position = lambda: position  # center position
        self.original_img = img
        self.edited_img = img.copy()
        self.init_angle = init_angle
        self.original_center_offset = Vector2.Cartesian(*center_offset)
        self.edited_center_offset = self.original_center_offset.copy()
        self.rect = self.edited_img.get_rect(center=add_tuples(self.position(), self.edited_center_offset))

    def rotate(self, angle):
        self.edited_img = pygame.transform.rotate(self.original_img, -angle).convert_alpha()
        self.edited_center_offset = self.original_center_offset.rotated(angle)
        self.rect = self.edited_img.get_rect(center=add_tuples(self.position(), self.edited_center_offset))

    def blit_image(self):
        self.rect.center = add_tuples(self.position(), self.edited_center_offset)
        # r = self.rect.copy()
        # r.topleft -= Camera.scroller
        Camera.blit(self.edited_img, add_tuples(self.rect.topleft, self.edited_center_offset) - Camera.scroller)
        # pygame.draw.rect(Camera.screen, Color('red'), r, 5)
        return self.edited_img


class FlippableRotatedImage:
    def __init__(self, img: pygame.Surface, init_angle, pivot_offset, sprite_rect_offset, sprite_rect,
                 original_direction):
        """
        :param img:  image to use (Surface)
        :param init_angle:  initial angle (int)
        :param pivot_offset: center of the "Circular Motion" position relative to img  (Tuple[int,int])
        :param sprite_rect_offset:  position of the pivot_offset relative to the sprite rect  (Tuple[int,int])
        :param sprite_rect: rect who will be mirrored (Rect)
        :param original_direction:  the direction which within it the above parameters were given
        """
        img = img.convert_alpha()
        self.sprite_rect = sprite_rect
        self.original_direction = original_direction
        if original_direction == Direction.right:
            self.right_image = RotatableImage(img, init_angle, pivot_offset,
                                              lambda: add_tuples(sprite_rect.topleft, sprite_rect_offset))
            new_position = sprite_rect.width - sprite_rect_offset[0], sprite_rect_offset[1]
            new_offset = mul_tuple(pivot_offset, -1)
            self.left_image = RotatableImage(pygame.transform.flip(img, True, False).convert_alpha(), init_angle,
                                             new_offset,
                                             lambda: add_tuples(sprite_rect.topleft, new_position))
        elif original_direction == Direction.left:
            self.left_image = RotatableImage(img, init_angle, pivot_offset,
                                             lambda: add_tuples(sprite_rect.topleft, sprite_rect_offset))
            new_position = sprite_rect.width - sprite_rect_offset[0], sprite_rect_offset[1]
            new_offset = mul_tuple(pivot_offset, -1)
            self.right_image = RotatableImage(pygame.transform.flip(img, True, False).convert_alpha(), init_angle,
                                              new_offset,
                                              lambda: add_tuples(sprite_rect.topleft, new_position))

    def rotate(self, angle):
        if self.original_direction == Direction.right:
            self.right_image.rotate(angle)
            self.left_image.rotate(-angle)
        else:
            self.left_image.rotate(angle)
            self.right_image.rotate(-angle)

    def blit_image(self, _direction):
        if _direction in Direction.rights:
            r = self.right_image.rect.copy()
            self.right_image.blit_image()
        elif _direction in Direction.lefts:
            r = self.left_image.rect.copy()
            self.left_image.blit_image()
        # r.topleft = r.topleft - Camera.scroller
        # draw.rect(Camera.screen, Color('red'), r, 5)


class Man(AdvancedSprite):
    """Main player sprites"""
    # just taking random image to get height and width after trans scale to be able to crop later (see lines 23/36)
    scale = 1 / 2.5
    idle_right_images = get_images_list(r"animation\fighter\PNG\PNG Sequences\Firing" + '\\*', scale)
    dying_right_images = get_images_list(r"animation\fighter\PNG\PNG Sequences\Dying" + '\\*', scale)
    dying_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), dying_right_images))
    move_right_images = get_images_list(r"animation\fighter\PNG\PNG Sequences\Run Firing" + '\\*', scale,
                                        sort_key=lambda x: int(x.split('\\\\')[-1].split(' ')[-1].split('.')[0]))
    move_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), move_right_images))

    idle_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), idle_right_images))
    direction = {'right': 1, 'left': 0, 'idle': 2}
    CAPACITY = 4

    # hitbox = (x+55, y+35, self.width-125, self.height-45) # nothing special on those num, just Trial and error

    def __init__(self, x, y, jump_key, right_key, left_key, shoot_key, health_bar_colors, name):
        # hit boxes & moving
        self.moving_speed = 350

        self.walk_left_animation = Animation.by_images_list(Man.move_left_images, 30)  # Random number. should play with
        # it for best results
        self.walk_right_animation = Animation.by_images_list(Man.move_right_images, 30)
        self.dying_right_animation = Animation.by_images_list(Man.dying_right_images, 10, False)
        self.dying_left_animation = Animation.by_images_list(Man.dying_left_images, 10, False)
        self.idle_right_animation = Animation.by_images_list(Man.idle_right_images, 10)
        self.idle_left_animation = Animation.by_images_list(Man.idle_left_images, 10)

        rect = Man.idle_right_images[0].get_rect()  # just random. it will set again every time image changes
        rect.topleft = x, y
        super(Man, self).__init__(rect, controls.ManControl(left_key, right_key, jump_key, shoot_key, self,
                                                            Direction.idle_right, 0.5), 1, 10, health_bar_colors, 2)
        # super(Man, self).__init__(rect, controls.SimpleZombieControl(self, Direction.right), 1, health_bar_colors, 10,
        #                           resistance_length=2)

        # visuals
        self.name = name

        # jumping & physics
        # self.last_rect = self.rect
        self.hit_timer = Timer(1)

    def final_dead(self):
        pass

    def draw(self):
        dead = False
        if not self.is_dead:
            if self.control.direction in (Direction.right, Direction.jumping_right):  # moving right
                self.image = self.walk_right_animation.get_image()
            elif self.control.direction in (Direction.left, Direction.jumping_left):
                self.image = self.walk_left_animation.get_image()
            elif self.control.direction == Direction.idle_left:
                self.image = self.idle_left_animation.get_image()
            elif self.control.direction == Direction.idle_right:
                self.image = self.idle_right_animation.get_image()

        elif self.visible:  # if man died but still visible:
            if self.control.direction in Direction.lefts:
                self.image = self.dying_left_animation.get_image()
            elif self.control.direction in Direction.rights:
                self.image = self.dying_right_animation.get_image()
            x, y = self.rect.topleft
            self.rect = self.image.get_rect()
            self.rect.topleft = (x, y)
            dead = True
            # self.draw_rect()
        else:
            self.final_dead()  # if man is completely dead
        super(Man, self).draw(not dead)


class Zombie(AdvancedSprite):
    scale = 1 / 2.5
    moving_right_images = get_images_list(r"animation\zombie\PNG\Tiny "
                                          r"Zombie 01\PNG Sequences\Walking" + '\\*', scale)
    moving_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), moving_right_images))

    dying_right_images = get_images_list(r'animation\zombie\PNG\Tiny Zombie 01\PNG Sequences\Dying' + '\\*', scale)
    dying_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), dying_right_images))

    idle_right_images = get_images_list(r'animation\zombie\PNG\Tiny Zombie 01\PNG Sequences\idle' + '\\*', scale)
    idle_left_images = list(map(lambda k: pygame.transform.flip(k, True, False).convert_alpha(), idle_right_images))

    def __init__(self, x, y):
        rect = Zombie.moving_right_images[0].get_rect()
        rect.topleft = x, y

        self.walk_right_animation = Animation.by_images_list(Zombie.moving_right_images, 3)
        self.walk_left_animation = Animation.by_images_list(Zombie.moving_left_images, 3)

        self.dying_right_animation = Animation.by_images_list(Zombie.dying_right_images, 3, False)
        self.dying_left_animation = Animation.by_images_list(Zombie.dying_left_images, 3, False)

        self.idle_right_animation = Animation.by_images_list(Zombie.idle_right_images, 3)
        self.idle_left_animation = Animation.by_images_list(Zombie.idle_left_images, 3)
        self.moving_speed = 150
        self.damage = 3

        self.hit_strength = 1000
        self.idle_hit_angle = 40

        super(Zombie, self).__init__(rect, controls.SimpleZombieControl(self, 1), 1, 10, ((4, 3, 137), (66, 165, 245)),
                                     1)
        # super(Zombie, self).__init__(rect, controls.ManControl(K_LEFT, K_RIGHT, K_SPACE, K_RETURN, self,
        #                                                        Direction.idle_right, Timer(2)), 1, ((4, 3, 137), (66, 165, 245)), 10)

    def draw(self):
        if not self.is_dead:
            if self.control.direction == Direction.right:  # moving right
                self.image = self.walk_right_animation.get_image()
            elif self.control.direction == Direction.left:
                self.image = self.walk_left_animation.get_image()
            elif self.control.direction == Direction.idle_left:
                self.image = self.idle_left_animation.get_image()
            elif self.control.direction == Direction.idle_right:
                self.image = self.idle_right_animation.get_image()

        elif self.visible:  # if man died but still visible:
            if self.control.direction in Direction.lefts:
                self.image = self.dying_left_animation.get_image()
            elif self.control.direction in Direction.rights:
                self.image = self.dying_right_animation.get_image()
        else:
            self.final_dead()  # if man is completely dead

        super(Zombie, self).draw()

    def collision(self, other: AdvancedSprite):
        if self.is_dead:
            return

        if isinstance(other, Vehicle):
            if self.control.direction == Direction.right and other.rect.right > self.rect.right:
                self.control.direction = Direction.left
            elif self.control.direction == Direction.left and other.rect.left < self.rect.left:
                self.control.direction = Direction.right

        elif isinstance(other, AdvancedSprite) and other.resistance_timer.finished():
            other.hit_points -= self.damage
            if round(other.velocity.x, 2) == 0:
                if self.control.direction in Direction.lefts:
                    other.add_force(Vector2.Polar(self.hit_strength, 180 + self.idle_hit_angle), 'push')
                elif self.control.direction in Direction.rights:
                    other.add_force(Vector2.Polar(self.hit_strength, 360 - self.idle_hit_angle), 'push')
            else:
                if self.rect.center[0] > other.rect.center[0]:  # The zombie is to the right of other
                    other.velocity.reset()
                    other.add_force(Vector2.Polar(self.hit_strength, 180 + self.idle_hit_angle), 'push')
                elif self.rect.center[0] < other.rect.center[0]:  # The zombie is to the left of other
                    other.velocity.reset()
                    other.add_force(Vector2.Polar(self.hit_strength, 360 - self.idle_hit_angle), 'push')
                else:
                    other.velocity.reset()
                    other.add_force(Vector2.Polar(self.hit_strength, 270), 'push')

            other.resistance_timer.activate()
            t = Timer(3, True)
            # other.control.in_control = UntilCondition(lambda: other.on_platform or t)
            other.control.in_control = UntilCondition(lambda: other.platform_collide or
                                                              (other.sprite_collide and not
                                                              isinstance(other.sprite_collide, Zombie)) or t)


class Bullet(BaseSprite):
    def __init__(self, rect, damage, travel_distance):
        super(Bullet, self).__init__(rect, controls.NoMoveControl(self, None), 1)
        self.damage = damage
        self.travel_distance = travel_distance
        self.first_frame = True

    def __str__(self):
        return super(Bullet, self).__str__() + f', travel_distance{self.travel_distance}'

    def update_position(self, axis, time_delta):
        if axis == Direction.vertical:
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
        if direction == Direction.vertical:
            self.kill()


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


class Missile(Bullet):
    DAMAGE = 1
    TRAVEL_DISTANCE = 1500
    MISSILE_IMAGE = pygame.image.load(r'images\missile.png').convert_alpha()
    MISSILE_IMAGE = smooth_scale_image(MISSILE_IMAGE, 1.5)

    def __init__(self, init_direction, tank: Tank, shoot_force):
        turret_angle = tank.turret_angle
        turret_obj = tank.turret_image
        r = Missile.MISSILE_IMAGE.get_rect()

        if init_direction in Direction.rights:
            turret_rect = turret_obj.right_image.rect
            if turret_angle > 0:
                r.bottomleft = turret_rect.topright
            elif turret_angle <= 0:
                r.topleft = turret_rect.bottomright

        elif init_direction in Direction.lefts:
            turret_rect = turret_obj.left_image.rect
            if turret_angle > 0:
                r.bottomright = turret_rect.topleft
            elif turret_angle <= 0:
                r.topright = turret_rect.bottomleft
        super(Missile, self).__init__(r, Missile.DAMAGE, Missile.TRAVEL_DISTANCE)
        self.missile_image = RotatableImage(Missile.MISSILE_IMAGE, 0, (0, 0), lambda: self.rect.topleft)
        self.total_movement = 0
        self.killed = False
        self.shoot_force = shoot_force
        self.rect_collision = False

    def draw(self):
        self.missile_image.rotate(int(self.velocity.theta))
        self.image = self.missile_image.blit_image()
        self.rect.width = self.missile_image.rect.width
        self.rect.height = self.missile_image.rect.height
        self.rect.topleft = self.missile_image.rect.topleft
        # self.draw_rect()

    def _update(self, control_dict):
        if self.first_frame:
            self.add_force(self.shoot_force, "shoot", True)
        self.total_movement = 0
        self.operate_gravity()
        super(Missile, self)._update(control_dict)
        self.travel_distance -= math.sqrt(self.total_movement)
        self.first_frame = False

    def update_position(self, axis, time_delta):
        if self.travel_distance <= 0:
            self.kill()
        self.total_movement += abs(self.velocity.x * time_delta) ** 2
        super(Missile, self).update_position(axis, time_delta)

    def kill(self):
        if not self.killed:
            Camera.shake()
            player.play_sound(Sound.Sounds.explosion)
            Camera.add_particle(Particale.Explosion, self.rect.center, collide_function=self.explosion_collide)
            super(Missile, self).kill()
            self.killed = True

    def explosion_collide(self, other):
        if isinstance(other, AdvancedSprite) and not other.is_dead:
            if other.resistance_timer.finished():
                other.hit_points -= self.damage
                other.resistance_timer.activate()

    def collision(self, other):
        if self.first_frame:
            return
        if (isinstance(other, AdvancedSprite)) and not other.is_dead:
            if other.resistance_timer.finished():
                other.hit_points -= self.damage
                other.resistance_timer.activate()
            self.kill()
            return False
        elif isinstance(other, Bullet):
            self.kill()
            return False


class MissileMagazine(pygame.sprite.Group):
    magazines_list = []

    def __init__(self, shot_delay, capacity, tank, damage=GunBullet.DAMAGE):
        super(MissileMagazine, self).__init__()
        self.capacity = capacity
        self.shot_timer = Timer(shot_delay)
        self.damage = damage
        self.tank = tank
        Magazine.magazines_list.append(self)

    def add_bullet(self, velocity_vector):
        if self.shot_timer.finished() and not self.full():
            self.shot_timer.activate()
            bull = Missile(self.tank.control.direction, self.tank, velocity_vector)
            self.add(bull)
            return bull
        return None

    def full(self):
        return len(self) >= self.capacity


class Magazine(pygame.sprite.Group):
    magazines_list = []

    def __init__(self, clr, size, shot_delay, capacity, damage=GunBullet.DAMAGE):
        super(Magazine, self).__init__()
        self.capacity = capacity
        self.shot_timer = Timer(shot_delay)
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


import Particale  # otherwise they are colliding


def tick(elapsed, clock, keys=pygame.key.get_pressed()):
    # print(len(BaseSprite.sprites_list))
    start = time()
    BaseSprite.update_states(keys, elapsed)
    Camera.reset_frame()
    # BaseSprite.check_sprite_collision()
    Particale.Particle.check_all_collision()
    BaseSprite.update_all()
    BaseSprite.check_sprite_collision()
    Particale.Particle.update_all()
    Tile.update_all()
    Camera.scroller.update()
    UntilCondition.update_all()
    # Timer.tick_all(clock.get_fps())
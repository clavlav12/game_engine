import Engine.structures as structures
from glob import glob as files_in_dir
from collections import namedtuple
from win32api import GetSystemMetrics
from itertools import repeat
from time import time
import pygame
import math

Tile: type = type
Sprite: type = type
Air: type = type
clock: type = type


def init(TileClass, AirClass, SpriteClass, clockInstance):
    global Tile
    global Sprite
    global Air
    global clock
    Tile = TileClass
    Air = AirClass
    clock = clockInstance
    Sprite = SpriteClass


def smooth_scale_image(img, scale):
    return pygame.transform.smoothscale(img, structures.mul_tuple(img.get_size(), scale)).convert_alpha()


def smooth_scale_images(lst, scale):
    return [smooth_scale_image(i, scale) for i in lst]


def get_images_list(path, scale=None, crop_rect=None, sort_key=None):
    if sort_key:
        files = sorted(files_in_dir(path), key=sort_key)
    else:
        files = files_in_dir(path)
    lst = []
    for file in files:
        img = pygame.image.load(file)
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


class collision_manifold:
    def __init__(self, sprite1, sprite2, penetration, normal, collision, x_collision,
                 contact_points=None, contact_count=0):
        if contact_points is None:
            contact_points = [None, None]
            contact_count = 0
        self.contact_points = contact_points
        self.contact_count = contact_count
        self.sprite1 = sprite1
        self.sprite2 = sprite2
        self.penetration = penetration
        self.normal = normal
        self.collision = collision
        self.x_collision = x_collision

    def __str__(self):
        return str(self.collision)

    @classmethod
    def by_two_objects(cls, obj1, obj2):
        normal = cls.get_mid(obj2) - cls.get_mid(obj1)
        obj1_extent_x = obj1.rect.width / 2
        obj2_extent_x = obj2.rect.width / 2

        x_overlap = obj1_extent_x + obj2_extent_x - abs(normal.x)

        y_collision = False
        x_collision = False
        if x_overlap > 0:
            obj1_extent_y = obj1.rect.height / 2
            obj2_extent_y = obj2.rect.height / 2

            y_overlap = obj1_extent_y + obj2_extent_y - abs(normal.y)
            if y_overlap > 0:
                if x_overlap < y_overlap:
                    if normal.x < 0:
                        normal_normalized = structures.Vector2.Cartesian(-1, 0)
                    else:
                        normal_normalized = structures.Vector2.Cartesian(1, 0)
                    penetration = x_overlap
                    x_collision = True
                else:
                    if normal.y < 0:
                        normal_normalized = structures.Vector2.Cartesian(0, -1)
                    else:
                        normal_normalized = structures.Vector2.Cartesian(0, 1)
                    penetration = y_overlap
                    y_collision = True

                return cls(obj1, obj2, penetration, normal_normalized, True, x_collision)

        return cls(obj1, obj2, None, None, False, False)

    @staticmethod
    def get_mid(obj):
        if isinstance(obj, Sprite):
            return obj.position + (structures.Vector2.Point(obj.rect.size) / 2)
        else:  # Rect only no float position
            return obj.rect.topleft + (structures.Vector2.Point(obj.rect.size) / 2)

    def __bool__(self):
        return self.collision


def remove_id(dictionary: dict):
    dictionary.pop('id')
    return dictionary


class Map:
    instance = None

    def __init__(self, first_quadrant,
                 second_quadrant,
                 third_quadrant,
                 forth_quadrant,
                 tile_size
                 , *,
                 empty=False
                 ):
        assert Map.instance is None, "Two Maps?!"
        """
        :param mp: 2 dimensional list
        """
        self.first_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=x * tile_size, y=y * tile_size)
                                for x, kwargs in enumerate(row)] for y, row in enumerate(first_quadrant)]

        self.second_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=-x * tile_size, y=y * tile_size)
                                 for x, kwargs in enumerate(reversed(row))]
                                for y, row in enumerate(second_quadrant)]
        self.third_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=-x * tile_size, y=-y * tile_size)
                                for x, kwargs in enumerate(reversed(row))]
                               for y, row in enumerate(reversed(third_quadrant))]
        self.forth_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=x * tile_size, y=-y * tile_size)
                                for x, kwargs in enumerate(row)] for y, row in
                               enumerate(reversed(forth_quadrant))]
        # for i in self.first_quadrant:
        #     for a in i:
        #         if a.id == 1:
        #             print(a.rect.top)

        # print(*[['0' if isinstance(tile, air) else '1' for tile in column] for column in self.map], sep='\n')
        self.map_maps = {
            (1, 1): self.first_quadrant,
            (-1, 1): self.second_quadrant,
            (-1, -1): self.third_quadrant,
            (1, -1): self.forth_quadrant,

        }
        self.tile_size = tile_size

        self.empty = empty
        Map.instance = self

    def get_tile(self, x, y):
        return self.map_maps[(int(math.copysign(1, x)), int(math.copysign(1, y)))][abs(y)][abs(x)]

    @classmethod
    def No_Map(cls):
        cls([], [], [], [], 1, empty=True)

    @classmethod
    def from_file(cls, file):
        pass

    @singleton_classmethod
    def get_map(self, x, y):
        return self.map_maps[(int(math.copysign(1, x)), int(math.copysign(1, y)))]

    @singleton_classmethod
    def check_platform_collision(self, sprite, time_delta):
        if self.empty:
            return None, None

        x, y, width, height = sprite.position.x, sprite.position.y, sprite.rect.width, sprite.rect.height
        left = int(x // self.tile_size)
        right = int((x + width) // self.tile_size)
        top = int(y // self.tile_size)
        bottom = int((y + height) // self.tile_size)

        if (y + height) / self.tile_size == bottom:
            bottom -= 1
        if y / self.tile_size == top:
            top += 1
        if x / self.tile_size == left:
            left += 1
        if (x + width) / self.tile_size == right:
            right -= 1

        sprite.update_velocity_and_acceleration(time_delta)

        row, column = 0, 0
        called = []
        for column in range(top, bottom + 1):
            for row in range(left, right + 1):
                try:
                    tile = self.get_tile(row, column)
                    if not isinstance(tile, Air):
                        if sprite.rect_collision or \
                                pygame.sprite.collide_mask(tile, sprite):  # mask
                            collection = tile.group
                            if collection is not tile and collection in called:
                                continue
                            elif collection is not tile:
                                called.append(collection)

                            if callable(sprite.collision_manifold_generator):
                                collision = sprite.collision_manifold_generator(collection, sprite)
                            else:
                                collision = collision_manifold.by_two_objects(collection, sprite)
                            if collision:
                                before = tile.sprite_collide(sprite,
                                                             collision
                                                             )
                                sprite.update_velocity_and_acceleration(time_delta)
                except IndexError:  # no collision
                    pass

        try:
            return tile, before
        except:
            return None, None


class DisplayMods:
    BASE_WIDTH = 1728
    BASE_HEIGHT = 972

    current_width = BASE_WIDTH
    current_height = BASE_HEIGHT

    MONITOR_WIDTH = GetSystemMetrics(0)
    MONITOR_HEIGHT = GetSystemMetrics(1)
    # MONITOR_WIDTH = 1680
    # MONITOR_HEIGHT = 1080
    MONITOR_RESOLUTION = (MONITOR_WIDTH, MONITOR_HEIGHT)

    @classmethod
    def get_resolution(cls):
        return cls.current_width, cls.current_height

    @classmethod
    def FullScreen(cls):
        return pygame.display.set_mode(cls.MONITOR_RESOLUTION, pygame.FULLSCREEN)

    @classmethod
    def FullScreenAccelerated(cls):
        return pygame.display.set_mode(cls.MONITOR_RESOLUTION, pygame.HWSURFACE)

    @classmethod
    def WindowedFullScreen(cls):
        return pygame.display.set_mode(cls.MONITOR_RESOLUTION, pygame.NOFRAME, display=0)

    @classmethod
    def Windowed(cls, size):
        cls.current_width, cls.current_height = size
        return pygame.display.set_mode((cls.current_width, cls.current_height))

    @classmethod
    def Resizable(cls, size):
        cls.current_width, cls.current_height = size
        return pygame.display.set_mode((cls.current_width, cls.current_height), pygame.RESIZABLE)


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


class Animation:
    """Collection class to make animations easier"""
    _key = object()

    def __init__(self, creation_key, parameter, fps, repeat, flip_x, flip_y, scale):
        if creation_key is not Animation._key:
            raise structures.PrivateConstructorAccess(f"Access denied to private constructor of class {Animation}")
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


class TileCollection:
    def __init__(self):
        self.rect = None

    def add_tile(self, tile):
        if self.rect is None:
            self.rect = pygame.Rect(*tile.rect)
        else:
            rect = tile.rect
            if rect.x == self.rect.x:
                self.rect.height += rect.height
            elif rect.x < self.rect.x:
                self.rect.left -= rect.width
            if rect.y == self.rect.y:
                self.rect.width += rect.width
            elif rect.y < self.rect.y:
                self.rect.top -= rect.top

    def sprite_collide(self, _sprite, collision):
        pass


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


class RotatableImageOld:
    def __init__(self, img: pygame.Surface, init_angle, center_offset, position: callable):
        if callable(position):
            self.position = position  # center position
        elif isinstance(position, tuple):
            if len(position) == 2:
                self.position = lambda: position  # center position
        self.original_img = img
        self.edited_img = img.copy()
        self.angle = None
        self.original_center_offset = structures.Vector2.Cartesian(*center_offset)
        self.edited_center_offset = self.original_center_offset.copy()
        self.rect = self.edited_img.get_rect(center=structures.add_tuples(self.position(), self.edited_center_offset))
        self.rotate(init_angle)

    def rotate(self, angle):
        if not angle == self.angle:
            self.angle = angle
            self.edited_img = pygame.transform.rotate(self.original_img, -angle).convert_alpha()
            self.edited_center_offset = self.original_center_offset.rotated(angle)
            self.rect = self.edited_img.get_rect(center=structures.add_tuples(self.position(), self.edited_center_offset))

    def blit_image(self):
        self.rect.center = structures.add_tuples(self.position(), self.edited_center_offset)
        # r = self.rect.copy()
        # r.topleft -= Camera.scroller
        Camera.blit(self.edited_img,
                    structures.add_tuples(self.rect.topleft, self.edited_center_offset) - Camera.scroller)
        # pygame.draw.rect(Camera.screen, Color('red'), r, 5)
        return self.edited_img


class RotatableImage:
    def __init__(self, img, init_angle, center_offset):
        self.original_img = img
        self.edited_img = img.copy()
        self.pivot = pygame.math.Vector2(center_offset[0], -center_offset[1])
        self.center_offset = center_offset

        w, h = self.original_img.get_size()
        self.box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]

        self.angle = None

        self.rotate(init_angle)
        self.angle = init_angle

    def rotate(self, angle, skip_optimisation=False):
        if not angle == self.angle or skip_optimisation:
            self.angle = angle
            self.box_rotate = box_rotate = [p.rotate(angle) for p in self.box]
            self.min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
            self.max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
            pivot_rotate = self.pivot.rotate(angle)
            self.pivot_move = pivot_rotate - self.pivot
            self.edited_img = pygame.transform.rotate(self.original_img, angle)

    def blit_image(self, center_position):
        origin = (center_position[0] - self.center_offset[0] + self.min_box[0] - self.pivot_move[0],
                  center_position[1] - self.center_offset[1] - self.max_box[1] + self.pivot_move[1])
        Camera.blit(self.edited_img,
                    origin - Camera.scroller)

        # pygame.draw.rect(Camera.screen, Color('red'), r, 5)
        return self.edited_img, origin


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
        if original_direction == structures.Direction.right:
            self.right_image = RotatableImageOld(img, init_angle, pivot_offset,
                                              lambda: structures.add_tuples(sprite_rect.topleft, sprite_rect_offset))
            new_position = sprite_rect.width - sprite_rect_offset[0], sprite_rect_offset[1]
            new_offset = structures.mul_tuple(pivot_offset, -1)
            self.left_image = RotatableImageOld(pygame.transform.flip(img, True, False).convert_alpha(), init_angle,
                                             new_offset,
                                             lambda: structures.add_tuples(sprite_rect.topleft, new_position))
        elif original_direction == structures.Direction.left:
            self.left_image = RotatableImageOld(img, init_angle, pivot_offset,
                                             lambda: structures.add_tuples(sprite_rect.topleft, sprite_rect_offset))
            new_position = sprite_rect.width - sprite_rect_offset[0], sprite_rect_offset[1]
            new_offset = structures.mul_tuple(pivot_offset, -1)
            self.right_image = RotatableImageOld(pygame.transform.flip(img, True, False).convert_alpha(), init_angle,
                                              new_offset,
                                              lambda: structures.add_tuples(sprite_rect.topleft, new_position))

    def rotate(self, angle):
        if self.original_direction == structures.Direction.right:
            self.right_image.rotate(angle)
            self.left_image.rotate(-angle)
        else:
            self.left_image.rotate(angle)
            self.right_image.rotate(-angle)

    def blit_image(self, _direction):
        if _direction in structures.Direction.rights:
            r = self.right_image.rect.copy()
            self.right_image.blit_image()
        elif _direction in structures.Direction.lefts:
            r = self.left_image.rect.copy()
            self.left_image.blit_image()
        # r.topleft = r.topleft - Camera.scroller
        # draw.rect(Camera.screen, Color('red'), r, 5)


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
            cls.scroller = structures.Scroller(
                lambda: (pygame.display.Info().current_h, pygame.display.Info().current_w),
                DisplayMods.get_resolution(), starting_position=scroller__starting_position,
                minx=0, maxx=0,
                miny=0, maxy=0)
        elif scroller_type == 'dynamic':
            cls.scroller = structures.Scroller(
                lambda: (pygame.display.Info().current_w / 2, pygame.display.Info().current_h / 2),
                DisplayMods.get_resolution(), starting_position=scroller__starting_position, )
        elif scroller_type == 'half dynamic':
            maxx, minx, maxy, miny = scroller_edges
            cls.scroller = structures.Scroller(
                lambda: (pygame.display.Info().current_h, pygame.display.Info().current_w),
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
            r = sur.get_rect(center=structures.mul_tuple(cls.screen.get_size(), 0.5))
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
    def post_process(cls, sprites_list):
        for txt in cls.displayed_text:
            cls.blit(txt.text, txt.position)
        if cls.display_fps:
            fps_surface = cls.fps_font.render(str(round(clock.get_fps())) + ', ' + str(len(sprites_list)),
                                              True, pygame.Color('white'))
            cls.blit(fps_surface, (5, 5))
        cls.real_screen.blit(cls.screen, next(cls.shake_offset))
        if cls.save:
            pygame.image.save(cls.screen, 'saved.png')
            quit()

    @classmethod
    def reset_frame(cls):
        cls.screen.fill(cls.background)

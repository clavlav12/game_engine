import Engine.structures as structures
from glob import glob as files_in_dir
from collections import namedtuple
from win32api import GetSystemMetrics
from itertools import repeat
from time import time
import os
import pygame
import math

Tile: type = type
Sprite: type = type
Air: type = type
clock: type = type


def init(TileClass, AirClass, SpriteClass, clockInstance):
    """Initiate the file to prevent recursive importing"""
    global Tile
    global Sprite
    global Air
    global clock
    Tile = TileClass
    Air = AirClass
    clock = clockInstance
    Sprite = SpriteClass


def smooth_scale_image(img, scale):
    """Smoothly scales an image by scale "scale" """
    return pygame.transform.smoothscale(img, [int(x) for x in structures.mul_tuple(img.get_size(), scale)])


def smooth_scale_images(lst, scale):
    """Smoothly scales a list of images by scale "scale" """
    return [smooth_scale_image(i, scale) for i in lst]


def get_images_list(path, scale=None, crop_rect=None, sort_key=None) -> list:
    """
    Returns an image list by folder/reg expression
    :param sort_key: a key to sort the list by
    :param crop_rect: a rect to crop the images by
    :param scale: a scale to scale the images by
    :param path: path to directory / reg expression
    """
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
            img = pygame.transform.smoothscale(img, (int(wid * scale), int(hei * scale)))
        if crop_rect:
            img = img.subsurface((crop_rect.x, crop_rect.y, img.get_width - crop_rect.width, img.get_height -
                                  crop_rect.height))
        lst.append(img)
    return lst


def singleton_classmethod(function):
    """Binds the instance to the classmethod"""
    def inner(*args, **kwargs):
        assert Map.instance is not None, "No Map"
        if args and isinstance(args[0], Map):
            return function(*args, **kwargs)
        else:
            return function(Map.instance, *args, **kwargs)

    return inner


def remove_id(dictionary: dict):
    """Removes the key id and returns the dictionary"""
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
        self.tile_size = tile_size
        self.empty = empty
        Map.instance = self

        self.first_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=x * tile_size, y=y * tile_size)
                                for x, kwargs in enumerate(row)] for y, row in enumerate(first_quadrant)]

        self.second_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=-x * tile_size, y=y * tile_size)
                                 if not x == y == 0 else None
                                 for x, kwargs in enumerate(reversed(row))]
                                for y, row in enumerate(second_quadrant)]
        self.third_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=-x * tile_size, y=-y * tile_size)
                                if not x == y == 0 else None
                                for x, kwargs in enumerate(reversed(row))]
                               for y, row in enumerate(reversed(third_quadrant))]
        self.forth_quadrant = [[Tile.get_tile(kwargs['id'])(**remove_id(kwargs), x=x * tile_size, y=-y * tile_size)
                                if not x == y == 0 else None
                                for x, kwargs in enumerate(row)]
                               for y, row in
                               enumerate(reversed(forth_quadrant))]

        self.map_maps = {
            (1, 1): self.first_quadrant,
            (-1, 1): self.second_quadrant,
            (-1, -1): self.third_quadrant,
            (1, -1): self.forth_quadrant,

        }

    def get_tile(self, x, y):
        """Returns a tile by x and y coordinates"""
        return self.map_maps[(int(math.copysign(1, x)), int(math.copysign(1, y)))][abs(y)][abs(x)]

    @classmethod
    def No_Map(cls):
        """Empty map"""
        cls([], [], [], [], 1, empty=True)

    @classmethod
    def from_file(cls, file):
        """Implement later. load a map from a file"""

    @singleton_classmethod
    def get_map(self, x, y):
        """Get a quadrant by x and y unit coordinates"""
        return self.map_maps[(int(math.copysign(1, x)), int(math.copysign(1, y)))]

    @singleton_classmethod
    def check_platform_collision(self, sprite):
        """Check for collision with sprite"""
        if self.empty:
            return None, None

        x, y, width, height = sprite.position.x, sprite.position.y, sprite.rect.width, sprite.rect.height
        left = int((x - width // 2) // self.tile_size)
        right = int((x + width // 2) // self.tile_size)
        top = int((y - height // 2) // self.tile_size)
        bottom = int((y + height // 2) // self.tile_size)

        called = []
        for column in range(top, bottom + 1):
            for row in range(left, right + 1):
                try:
                    current_tile = self.get_tile(row, column)
                    if not isinstance(current_tile, Air):
                        tile = current_tile
                        collider = tile.collider & sprite.collider

                        if collider.tile_collision_by_rect or pygame.sprite.collide_mask(sprite, tile):  ## tile group?!
                            collection = tile.group

                            if collection in called:
                                continue

                            tile.group.set_reference(tile)
                            manifold = collider.manifold_generator(sprite, tile.group)

                            if (manifold is None) or manifold.collision:
                                called.append(collection)

                                tile.sprite_collide(sprite, manifold)
                except IndexError:  # no collision
                    pass

        try:
            if isinstance(tile, Air):
                tile = None
            return tile
        except NameError:
            return None


def screen_maker(func):
    """Decorator - creates a screen, then updates class's properties"""
    def inner(*args, **kwargs):
        val = func(DisplayMods, *args, **kwargs)
        DisplayMods.current_width, DisplayMods.current_height = val.get_size()
        return val
    return inner


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
        """Returns the current resolution of the screen"""
        return cls.current_width, cls.current_height

    @screen_maker
    def FullScreen(cls):
        """Generates a fullscreen display"""
        return pygame.display.set_mode(cls.MONITOR_RESOLUTION, pygame.FULLSCREEN)

    @screen_maker
    def FullScreenAccelerated(cls):
        """Generates a fullscreen display, hardware accelerated."""
        return pygame.display.set_mode(cls.MONITOR_RESOLUTION, pygame.HWSURFACE)

    @screen_maker
    def WindowedFullScreen(cls):
        """Generates a windowed fullscreen display"""
        return pygame.display.set_mode(cls.MONITOR_RESOLUTION, pygame.NOFRAME, display=0)

    @screen_maker
    def Windowed(cls, size):
        """Generates a windowed display"""
        cls.current_width, cls.current_height = size
        return pygame.display.set_mode((cls.current_width, cls.current_height))

    @screen_maker
    def Resizable(cls, size):
        """Generates a resizable windowed display"""
        cls.current_width, cls.current_height = size
        return pygame.display.set_mode((cls.current_width, cls.current_height), pygame.RESIZABLE)

    @screen_maker
    def NoWindow(cls):
        """No window (to use on server)"""
        return EmptyDisplayMod()


class EmptyDisplayMod:
    """Mimics the pygame.display class"""
    def fill(self, _):
        pass

    def copy(self):
        return self

    def blit(self, _, __):
        pass

    def get_size(self):
        return DisplayMods.current_width, DisplayMods.current_height

    def __bool__(self):
        return False


class HealthBar:
    HEIGHT_CONST = 0.2

    def __init__(self, pos_color, neg_color, advanced_sprite):
        self.sprite = advanced_sprite
        self.neg_color = neg_color
        self.pos_color = pos_color

        self.bar_height = round(self.sprite.rect.height * HealthBar.HEIGHT_CONST)
        self.bar_width = self.sprite.rect.width
        self.negative_bar_rect = pygame.Rect(self.sprite.rect.x, self.sprite.rect.y - self.bar_height, self.bar_width,
                                             self.bar_height)
        self.positive_bar_rect = pygame.Rect(self.sprite.rect.x, self.sprite.rect.y - self.bar_height, self.bar_width *
                                             (self.sprite.base_hit_points // self.sprite.hit_points), self.bar_height)

    def draw(self):
        """
        Draws health bar to screen
        negative_bar -> stays the same size
        positive_bar -> decreases with hp
        """
        self.negative_bar_rect.center = self.sprite.rect.center
        self.negative_bar_rect.bottom = self.sprite.rect.top
        self.negative_bar_rect.x -= Camera.scroller['x']
        self.negative_bar_rect.y -= Camera.scroller['y']
        self.positive_bar_rect.topleft = self.negative_bar_rect.topleft

        self.positive_bar_rect.width = max(
            round(self.bar_width * (self.sprite.hit_points / self.sprite.base_hit_points)), 0)

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
        # self.convert_alpha()
        assert bool(self.images_list), "image list is empty"
        self.pointer = 0
        self.frames_per_second = fps
        self.timer = Timer(1 / self.frames_per_second)
        self.repeat = repeat

    # def convert_alpha(self):
    #     self.images_list = ImageList([AutoConvertSurface(i) for i in self.images_list])

    @classmethod
    def by_images_list(cls, lst, frames_per_image=1, repeat=True, flip_x=False, flip_y=False, scale=1):
        """
        Generates an Animation object from an image list
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
        Generates an Animation object from a directory
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
        """Next image in the animation list"""
        if not self.timer.is_counting:
            if self.timer.finished():
                self.update_pointer()
                self.timer.activate()
        return self.images_list[self.pointer]  # ??

    def update_pointer(self):
        """Updates the pointer. If it's too big - go back to the start or stay on the last frame"""
        self.pointer += 1
        if self.pointer >= len(self.images_list):  # ??
            if self.repeat:
                self.pointer = 0
            else:
                self.pointer -= 1
            return True
        return False

    def reset(self):
        """Takes the pointer back to the beginning"""
        self.pointer = 0

    def finished(self):
        """Returns true if the animation is done and not set to repeat"""
        return (not self.repeat) and self.pointer == len(self.images_list) - 1  # ??

    def __next__(self):
        return self.get_image()

    def get_next_size(self):
        """Returns the size of the next image"""
        return self.images_list[self.pointer].get_size()

    def __len__(self):
        return len(self.images_list)


class TileCollection(pygame.sprite.Sprite):
    collections = []

    def __init__(self):
        self.rect = None
        self.reference = None
        self.collections.append(self)
        super(TileCollection, self).__init__()

    def update(self):
        """Called when the collection is changed. Updates the mask"""
        self.mask = pygame.mask.Mask(self.rect.size, True)

    def set_reference(self, tile):
        """Set the reference tile to "tile" """
        self.reference = tile

    def add_tile(self, tile):
        """Adds a tile to the group"""
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
            self.update()

    def sprite_collide(self, _sprite, collision):
        """Called on collision with a sprite"""


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
        """Reset the clock"""
        self.start_time = time()

    def activate(self, new_time=None):
        """Activates the clock"""
        if new_time:
            self.delay = new_time
        else:
            self.delay = self.base_delay
        self.start_time = time()
        self._is_counting = True

    def __bool__(self):
        return self.delay < (time() - self.start_time)

    def finished(self):
        """Returns true if the timer is done"""
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
        """Rotates the image"""
        if not angle == self.angle:
            self.angle = angle
            if Camera.screen:
                self.edited_img = pygame.transform.rotate(self.original_img, -angle).convert_alpha()
                self.edited_center_offset = self.original_center_offset.rotated(angle)

            self.rect = self.edited_img.get_rect(
                center=structures.add_tuples(self.position(), self.edited_center_offset))

    def blit_image(self):
        """Blits the image"""
        self.rect.center = structures.add_tuples(self.position(), self.edited_center_offset)
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
        """Rotates the image"""
        if not angle == self.angle or skip_optimisation:
            self.angle = angle
            self.box_rotate = box_rotate = [p.rotate(angle) for p in self.box]
            self.min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
            self.max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
            pivot_rotate = self.pivot.rotate(angle)
            self.pivot_move = pivot_rotate - self.pivot
            self.edited_img = pygame.transform.rotate(self.original_img, angle)

    def blit_image(self, center_position, blit_to_camera=True):
        """Blits the image"""
        origin = (center_position[0] - self.center_offset[0] + self.min_box[0] - self.pivot_move[0],
                  center_position[1] - self.center_offset[1] - self.max_box[1] + self.pivot_move[1])

        if blit_to_camera:
            Camera.blit(self.edited_img, origin - Camera.scroller)

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

            im = pygame.transform.flip(img, True, False)
            if Camera.screen:
                im = im.convert_alpha()
            self.right_image = RotatableImageOld(im, init_angle,
                                                 new_offset,
                                                 lambda: structures.add_tuples(sprite_rect.topleft, new_position))

    def rotate(self, angle):
        """Rotates the image"""
        if self.original_direction == structures.Direction.right:
            self.right_image.rotate(angle)
            self.left_image.rotate(-angle)
        else:
            self.left_image.rotate(angle)
            self.right_image.rotate(-angle)

    def blit_image(self, _direction):
        """Blits the image"""
        if _direction in structures.Direction.rights:
            self.right_image.blit_image()
        elif _direction in structures.Direction.lefts:
            self.left_image.blit_image()


class Camera:
    """Static class to handle scroller out of this file"""
    fnt = pygame.font.SysFont('comicsansms', 45)
    Text = namedtuple('Text', ['text', 'position', 'signature'])
    Image = namedtuple('Image', ['image', 'position', 'blit_time', 'start_time'])
    BlitOrder = namedtuple('BlitOrder', ['order', 'blit_time', 'start_time'])
    displayed_text = {}  # signature: Text(text, position, signature)
    scroller = None
    screen = None
    real_screen = None
    shake_offset = repeat((0, 0))
    background = (20, 24, 82)
    save = False
    display_fps = True
    fps_font = pygame.font.SysFont('comicsansms', 12)
    default_font = pygame.font.SysFont('Arial', 24)

    images = []
    blits = []

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
        os.environ['SDL_VIDEO_CENTERED'] = '1'

    @classmethod
    def blit_continuous_image(cls, image, position, time_to_blit):
        """Blit an image for a "time to blit" seconds long"""
        cls.images.append(cls.Image(image, position, time_to_blit, time()))

    @classmethod
    def add_blit_order(cls, function, time_to_blit):
        """A function called in the end of the frame to blit something to the screen"""
        cls.blits.append(cls.BlitOrder(function, time_to_blit, time()))

    @classmethod
    def set_scroller_position(cls, position, smooth_move=False):
        """Updates the scoller position"""
        cls.scroller.set_position(position, smooth_move)

    @classmethod
    def get_scroller(cls):
        """Returns the scroller"""
        return cls.scroller

    @staticmethod
    def add_particle(particle, *args, **kwargs):
        """Adds a particle to the screen"""
        particle(*args, **kwargs)

    @classmethod
    def display_text(cls, text: str, position, signature, font=None,
                     antialais=True, color=pygame.Color('red'), bg=None):
        """Display a text to the screen until removed"""
        if font is None:
            font = cls.default_font
        sur = font.render(text, antialais, color, bg)
        if position == 'center':
            r = sur.get_rect(center=structures.mul_tuple(cls.screen.get_size(), 0.5))
            position = r.topleft

        cls.displayed_text[signature] = cls.Text(sur, position, signature)

    @classmethod
    def remove_text(cls, signature):
        """Removes a displayed text from the screen"""
        for txt in cls.displayed_text.values():
            if txt.signature == signature:
                break
        else:  # if not break
            raise AttributeError(f"Signature {signature} not found")
        cls.displayed_text.pop(signature)

    @classmethod
    def shake(cls):
        """Shakes the screen"""
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
                yield x * s, 0
            for x in range(20, 0, 5):
                yield x * s, 0
            s *= -1
        while True:
            yield 0, 0

    @classmethod
    def blit(cls, surface, position):
        """Blits an image to the screen"""
        cls.screen.blit(surface, position)

    @classmethod
    def post_process(cls, sprites_list):
        """Blits texts, blit orders and continuous images. Also adds the shake effect"""
        for txt in cls.displayed_text.values():
            cls.blit(txt.text, txt.position)
        if cls.display_fps:
            fps_surface = cls.fps_font.render(str(round(clock.get_fps())) + ', ' + str(len(sprites_list)),
                                              True, pygame.Color('white'))
            cls.blit(fps_surface, (5, 5))
        if cls.images:
            new = cls.images.copy()
            for image in new:
                if image.start_time - time() > image.blit_time:
                    cls.images.remove(image)
                else:
                    cls.blit(image.image, image.position)

        if cls.blits:
            new = cls.blits.copy()
            for image in new:
                if image.blit_time is None:
                    cls.blits.remove(image)
                    try:
                        image.order(cls.screen)
                    except TypeError:
                        image.order()

                elif time() - image.start_time > image.blit_time:
                    cls.blits.remove(image)
                else:
                    try:
                        image.order(cls.screen)
                    except TypeError:
                        image.order()

        # for collection in TileCollection.collections:
        #     draw_rect(collection.rect)
        cls.real_screen.blit(cls.screen, next(cls.shake_offset))
        if cls.save:
            pygame.image.save(cls.screen, 'saved.png')
            quit()

        if cls.screen:
            pygame.display.flip()

    @classmethod
    def reset_frame(cls):
        """Resets the screen"""
        cls.screen.fill(cls.background)


class AutoConvertSurface:
    """Automatically converts a surface of a class"""
    __slots__ = 'image', 'converted'

    def __init__(self, image):
        self.image = image
        self.converted = False
        self.convert()

    def convert(self):
        """Converts image if possible"""
        try:
            self.image = self.image.convert_alpha()
            self.converted = True
            print("converted")
        except pygame.error:
            print("not converted")
            pass

    def __get__(self, instance, owner):
        """Tries to convert and return the best image it can"""
        if not self.converted:
            self.convert()
        return self.image

    def get_size(self):
        """Returns the size of self.image"""
        return self.image.get_size()


class ImageHolder:
    __slots__ = 'image', 'converted'

    def __init__(self, image):
        self.image = image
        self.converted = False

    def image_converted(self, new_image):
        """Replace old image with the new one and sets the converted flag to true"""
        self.image = new_image
        self.converted = True

    def get_image(self):
        """Returns the held image"""
        return self.image

    def __getitem__(self, item):
        if item == 0:
            return self.image
        elif item == 1:
            return self.converted
        else:
            raise IndexError()


class PrivateAutoConvertSurface:
    """Automatically converts a surface if an instance"""
    __slots__ = 'alpha', 'name'

    def __init__(self, alpha=True):
        self.alpha = alpha

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        """Tries to convert and return the best image it can"""
        try:
            image, converted = self.get_image_holder(instance)
        except KeyError:
            raise AttributeError(f"'{type(instance).__name__}' object has no attribute '{self.name}'")
        if converted or not Camera.screen:
            return image
        try:
            if self.alpha:
                converted = image.convert_alpha()
            else:
                converted = image.convert()

            self.image_converted(instance, converted)

        except pygame.error:
            pass

        return self.get_image(instance)

    def set_image(self, instance, image):
        """Sets the image of the instance to image"""
        instance.__dict__[self.name] = ImageHolder(image)

    def get_image(self, instance):
        """Returns the image of the instance"""
        return self.get_image_holder(instance).get_image()

    def is_converted(self, instance):
        """Returns whether or not the instance's image is converted"""
        return self.get_image_holder(instance).converted

    def get_image_holder(self, instance):
        """Returns the image holder"""
        return instance.__dict__[self.name]

    def image_converted(self, instance, new_image):
        """Replaces old instance image with a new one"""
        self.get_image_holder(instance).image_converted(new_image)

    def __set__(self, instance, value):
        self.set_image(instance, value)


class ImageList(list):
    """
    List of descriptors
    """
    def __init__(self, initlist):
        super(ImageList, self).__init__(initlist)

    def __getitem__(self, index):
        return super(ImageList, self).__getitem__(index).__get__(None, type)

    def __setitem__(self, index, value):
        super(ImageList, self).__getitem__(index).__set__(None, type)

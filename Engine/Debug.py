import pygame as pg
import math
from Engine import pygame_structures


class DebugKey:
    def __init__(self, key=None, is_pressed=False):
        self.key = pg.K_RETURN or key
        self.pressed = is_pressed

    def press(self):
        """
        press key
        """
        self.pressed = True

    def release(self):
        """
        release key
        """
        self.pressed = False

    def first_pressed(self):
        """
        Presses
        :return: True if key wasn't pressed before
        """
        was_pressed = self.pressed
        self.press()
        return not was_pressed

    def set_pressed(self, value):
        """
        Sets pressed state to value
        """
        self.pressed = value

    def set_pressed_auto(self):
        """
        Sets pressed state to proper value according to "keys"
        :return: True if key is pressed and wasn't pressed before (new press)
        """
        keys = pg.key.get_pressed()
        was_pressed = self.pressed
        self.pressed = keys[self.key]
        return (not was_pressed) and self.pressed

    def __str__(self):
        return str(self.key)

    def __bool__(self):
        return bool(self.pressed)

def draw_arrow(start, vec, lcolor=pg.Color('red'), tricolor=pg.Color('green'), trirad=3, thickness=2, scale=1):
    """
    Draws a Vector2 to the screen
    :param start: Origin of the vector
    :param vec: Vector2 to draw
    :param lcolor: Tale color
    :param tricolor: Head color
    :param trirad: Size of triangle (distance from triangle COM to the endpoint)
    :param thickness: Line width
    :param scale: Scales the vector (default argument is 1 - no scaling)
    :return:
    """
    end = tuple(start + vec * scale)
    start = tuple(start)
    rad = math.pi / 180
    pg.draw.line(pygame_structures.Camera.screen, lcolor, start, end, thickness)
    rotation = (math.atan2(start[1] - end[1], end[0] - start[0])) + math.pi / 2
    pg.draw.polygon(pygame_structures.Camera.screen, tricolor, ((end[0] + trirad * math.sin(rotation),
                                                                 end[1] + trirad * math.cos(rotation)),
                                                                (end[0] + trirad * math.sin(rotation - 120 * rad),
                                                                 end[1] + trirad * math.cos(rotation - 120 * rad)),
                                                                (end[0] + trirad * math.sin(rotation + 120 * rad),
                                                                 end[1] + trirad * math.cos(rotation + 120 * rad))))


def draw_circle(p, r=2, w=0, color=pg.Color('red')):
    """
    Draws a point
    :param p: point
    :param r: radius (default 2px)
    :param w: width (default filled)
    :param color: color of point (default red)
    """
    if isinstance(color, str):
        color = pg.Color(color)
    pg.draw.circle(pygame_structures.Camera.screen, color, tuple(p) - pygame_structures.Camera.scroller, r, w)


def get_circle(r=2, w=0, color=pg.Color('red')):
    """
    Same as draw_circle but returns an image instead
    """
    image = pg.Surface((r*2, r*2))
    if isinstance(color, str):
        color = pg.Color(color)
    pg.draw.circle(image, color, (r, r), r, w)
    return image


def draw_rect(r: pg.Rect, clr=pg.Color('red')):
    """
    Draws a rectangle
    :param r: Rectangle to draw
    :param clr: color (default red)
    """
    if not pygame_structures.Camera.screen:
        return
    r = r.copy()
    r.topleft = r.topleft - pygame_structures.Camera.scroller
    pg.draw.rect(pygame_structures.Camera.screen, clr, r, 1)


class WTFError(Exception):
    pass


debug = DebugKey()

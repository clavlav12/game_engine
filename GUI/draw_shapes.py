import pygame.gfxdraw as gfxdraw
from pygame import *
from enum import Enum
from abc import ABCMeta, abstractmethod
from GlobalUse import TRANSPARENT


def draw_filled_circle(surface, pos, radius, clr, aa=True):
    if aa:
        gfxdraw.aacircle(surface, *pos, radius, clr)
    gfxdraw.filled_circle(surface, *pos, radius, clr)


def draw_filled_ellipsis(surface, x, y, rx, ry, color):
    gfxdraw.aaellipse(surface, x, y, rx, ry, color)
    gfxdraw.filled_ellipse(surface, x, y, rx, ry, color)


def draw_rounded_rect(surface, clr, rect, radius=0.4):
    """
    AAfilledRoundedRect(surface,rect,color,radius=0.4)

    surface : destination
    rect    : rectangle
    color   : rgb or rgba
    radius  : 0 <= radius <= 1
    """

    rect = Rect(rect)
    clr = Color(*clr)
    alpha = clr.a
    clr.a = 0
    pos = rect.topleft
    rect.topleft = 0, 0
    rectangle = Surface(rect.size, SRCALPHA)
    circle = Surface([min(rect.size)*3]*2,SRCALPHA)
    draw.ellipse(circle,(0,0,0),circle.get_rect(),0)
    circle = transform.smoothscale(circle,[int(min(rect.size)*radius)]*2)

    radius = rectangle.blit(circle,(0,0))
    radius.bottomright = rect.bottomright
    rectangle.blit(circle, radius)
    radius.topright = rect.topright
    rectangle.blit(circle, radius)
    radius.bottomleft = rect.bottomleft
    rectangle.blit(circle, radius)

    rectangle.fill((0, 0, 0), rect.inflate(-radius.w, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius.h))

    rectangle.fill(clr, special_flags=BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=BLEND_RGBA_MIN)
    surface.blit(rectangle, pos)


# class Shapes(Enum):
#     circle = draw_filled_circle
#     ellipsis = draw_filled_ellipsis
#     rounded_rect = draw_rounded_rect
#     rect = draw.rect


class Shape:
    __metaclass__ = ABCMeta

    def __init__(self, rect, clr, angle=0):
        self.is_drawn = False
        self.rect = Rect(*rect)
        self.surface = Surface((self.rect.width, self.rect.height), SRCALPHA)
        self.color = Color(*clr)
        self.angle = angle
        self._first_draw()
        if angle != 0:
            self.surface = transform.rotate(self.surface, angle).convert_alpha()
        else:
            self.surface = Surface.convert_alpha(self.surface)
        self.is_drawn = True

    def draw(self, surface):
        surface.blit(self.surface, (self.rect.x, self.rect.y))

    @abstractmethod
    def _first_draw(self):
        """Should *not* be accessed by an outer function!!"""
        pass

    def to_image_and_pos(self) -> tuple:
        return self.surface, self.rect.topleft

    def __setattr__(self, key, value):
        super(Shape, self).__setattr__(key, value)
        if 'is_drawn' in self.__dict__ and self.is_drawn and key != 'is_drawn':
            self.__init__(self.rect, self.color, self.angle)

    def redraw(self):
        self.surface.fill(TRANSPARENT)
        self.is_drawn = False
        self._first_draw()
        self.is_drawn = True


class Rectangle(Shape):
    def _first_draw(self):
        draw.rect(self.surface, self.color, Rect(0, 0, self.rect.width, self.rect.height))


class RoundedRect(Shape):
    radius = 0.4

    def _first_draw(self):
        """
        AAfilledRoundedRect(surface,rect,color,radius=0.4)

        surface : destination
        rect    : rectangle
        color   : rgb or rgba
        radius  : 0 <= radius <= 1
        """
        original_rect = Rect(*self.rect)
        alpha = self.color.a
        self.color.a = 0
        self.rect.topleft = 0, 0
        rectangle = Surface(self.rect.size, SRCALPHA)
        circle = Surface([min(self.rect.size) * 3] * 2, SRCALPHA)
        draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
        circle = transform.smoothscale(circle, [int(min(self.rect.size) * RoundedRect.radius)] * 2)

        radius = rectangle.blit(circle, (0, 0))
        radius.bottomright = self.rect.bottomright
        rectangle.blit(circle, radius)
        radius.topright = self.rect.topright
        rectangle.blit(circle, radius)
        radius.bottomleft = self.rect.bottomleft
        rectangle.blit(circle, radius)

        rectangle.fill((0, 0, 0), self.rect.inflate(-radius.w, 0))
        rectangle.fill((0, 0, 0), self.rect.inflate(0, -radius.h))

        rectangle.fill(self.color, special_flags=BLEND_RGBA_MAX)
        rectangle.fill((255, 255, 255, alpha), special_flags=BLEND_RGBA_MIN)

        self.surface.blit(rectangle, (0, 0))

        self.rect = original_rect
        self.color.a = alpha

    def __setattr__(self, key, value):
        super(Shape, self).__setattr__(key, value)
        if 'is_drawn' in self.__dict__ and self.is_drawn and key != 'is_drawn':
            self.__init__(self.rect, self.color, self.angle)


class EllipseArguments(Enum):
    by_radius = 'by_radius'
    by_rect = 'by_rect'
    wrong_arguments = ''


class Ellipse(Shape):
    def __init__(self, *args, angle=None):
        arguments_type, is_angle = Ellipse.check_valid_args(args)
        if angle is None:
            if is_angle:
                angle = args[-1]
            else:
                angle = 0
        assert arguments_type.value, 'Unexpected arguments. expected: (x, y, rx, ry, color) or (rect, color).' \
                                     f'angle is also optional as a keyword\ngot {args}, angle={angle}'

        if arguments_type == EllipseArguments.by_rect:
            self.rx = args[0].brush_width // 2 - 5
            self.ry = args[0].height//2-5
            super(Ellipse, self).__init__(args[0], args[1], angle)

        elif arguments_type == EllipseArguments.by_radius:
            self.rx = args[2]
            self.ry = args[3]
            super(Ellipse, self).__init__(Rect(args[0], args[1], self.rx*2, self.ry*2), args[-1], angle)

    def _first_draw(self):
        # gfxdraw.aaellipse(self.surface, self.rect.width//2, self.rect.height//2, self.rx, self.ry , self.color)
        gfxdraw.filled_ellipse(self.surface, self.rect.width//2, self.rect.height//2, self.rx, self.ry, self.color)

    @staticmethod
    def check_valid_args(args):
        is_angle = False
        if isinstance(args[-1], int):
            if not isinstance(args[-2], (Color, tuple, list)):
                return EllipseArguments.wrong_arguments, is_angle
            else:
                is_angle = True
        if not is_angle and not isinstance(args[-1], (Color, tuple, list)):
            return EllipseArguments.wrong_arguments, is_angle
        if len(args) == 2 + is_angle:
            if not isinstance(args[0], (tuple, Rect)):
                return EllipseArguments.wrong_arguments, is_angle
            return EllipseArguments.by_rect, is_angle
        elif len(args) == 5 + is_angle:
            if not all([isinstance(args[i], int) for i in range(4)]):
                return EllipseArguments.wrong_arguments, is_angle
            return EllipseArguments.by_radius, is_angle
        return EllipseArguments.wrong_arguments, is_angle


class Circle(Shape):
    def __init__(self, *args, angle=0, radius=None):  # (x, y, radius, color) or (rect , color)
        arguments_type, is_angle = Circle.check_valid_args(args)
        if angle is None:
            if is_angle:
                angle = args[-1]
            else:
                angle = 0
        else:
            if is_angle:
                angle = args[-1]
            else:
                angle = 0
        assert bool(arguments_type.value), 'Unexpected arguments. expected: (x, y, radius, color) or ' \
                                           '(rect , color) when rect is a square.\n ' \
                                           'angle is also optional as a keyword. got ' + str(args)

        if arguments_type == EllipseArguments.by_rect:
            self.radius = maybe(radius)(args[0].brush_width // 4)
            super(Circle, self).__init__(args[0], args[1], angle)

        elif arguments_type == EllipseArguments.by_radius:
            self.radius = args[2]
            super(Circle, self).__init__(Rect(args[0], args[1], self.radius*2+1, self.radius*2+1), args[3], angle)

    def _first_draw(self):
        gfxdraw.aacircle(self.surface, self.radius, self.radius, self.radius, self.color)
        gfxdraw.filled_circle(self.surface, self.radius, self.radius, self.radius, self.color)

    @staticmethod
    def check_valid_args(args):
        is_angle = False
        if isinstance(args[-1], int):
            if not isinstance(args[-2], (Color, tuple, list)):
                return EllipseArguments.wrong_arguments, is_angle
            else:
                is_angle = True
        if not is_angle and not isinstance(args[-1], (Color, tuple, list)):
            return EllipseArguments.wrong_arguments, is_angle

        if len(args) == 2 + is_angle:
            if not isinstance(args[0], (tuple, Rect)):
                return EllipseArguments.wrong_arguments, is_angle
            return EllipseArguments.by_rect, is_angle
        elif len(args) == 4 + is_angle:
            if not all([isinstance(args[i], int) for i in range(3)]):
                return EllipseArguments.wrong_arguments, is_angle
            return EllipseArguments.by_radius, is_angle
        return EllipseArguments.wrong_arguments, is_angle


if __name__ == "__main__":
    print(Circle.__annotations__)
    # scr = display.set_mode((300, 300))
    # scr.fill(-1)
    # draw_rounded_rect(scr, (50, 50, 200, 50), (200, 20, 20), 0.5)
    # display.flip()
    # while event.wait().type != QUIT: pass

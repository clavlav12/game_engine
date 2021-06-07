from Engine.base_sprites import *
from Engine.structures import Vector2
import pygame as pg
import math


class Angle:
    def __init__(self, angle, velocity):
        self.angle = angle
        self.velocity = velocity
        self.torque = 0

    def add_torque(self, torque):
        if abs(torque) > 100:
            print(torque)
        self.torque += torque

    def step(self, dt):
        self.velocity += self.torque * dt
        self.angle += self.velocity * dt
        self.torque = 0

    def sin(self):
        return math.sin(self.angle)

    def cos(self):
        return math.cos(self.angle)

    def __add__(self, other):
        if isinstance(other, Angle):
            return Angle(self.angle + other.angle, 0)
        elif isinstance(other, (int, float)):
            return self.angle + other
        return NotImplemented

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if isinstance(other, Angle):
            return Angle(self.angle - other.angle, 0)
        elif isinstance(other, (int, float)):
            return self.angle - other
        return NotImplemented

    def __rsub__(self, other):
        return - self + other

    def __neg__(self):
        return Angle(-self.angle, 0)

    def __mul__(self, other):
        if isinstance(other, (float, int)):
            return Angle(self.angle * other, 0)
        return NotImplemented

    def __rmul__(self, other):
        return self * other


class DebugControl(controls.BaseControl):
    def __init__(self, *args, **kwargs):
        super(DebugControl, self).__init__(*args, **kwargs)
        self.n = 0
        self.clr = get_colors()

    def move(self, **kwargs):
        keys = kwargs['keys']

        if keys[pg.K_d]:
            self.sprite.color = self.clr[int(self.n * 8 / len(self.clr)) % len(self.clr)]
            self.n += 1

class DoublePendulum(BaseSprite):
    def __init__(self, origin, a1, a2, l1, l2, m1, m2, color=pg.Color('black')):
        self.origin = Vector2.Point(origin)
        self.a1 = Angle(a1, 0)
        self.a2 = Angle(a2, 0)
        self.l1 = l1
        self.l2 = l2
        self.m1 = m1
        self.m2 = m2
        self.color = color

        super(DoublePendulum, self).__init__(self.get_rect(), DebugControl(self), m1 + m2)

    def get_rect(self):
        p1 = self.origin
        p2 = self.get_pendulum_position(self.origin, self.a1, self.l1)
        p3 = self.get_pendulum_position(p2, self.a2, self.l2)

        min_x = min(p1, p2, p3, key=lambda v: v.x).x
        min_y = min(p1, p2, p3, key=lambda v: v.y).y
        max_x = max(p1, p2, p3, key=lambda v: v.x).x
        max_y = max(p1, p2, p3, key=lambda v: v.y).y

        return pg.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    @staticmethod
    def get_pendulum_position(origin: Vector2, angle: Angle, length):
        return origin.add_point((angle.sin() * length, angle.cos() * length))

    def update_kinematics(self, time_delta):
        self.first_torque()
        self.second_torque()
        self.a1.step(time_delta)
        self.a2.step(time_delta)
        super(DoublePendulum, self).update_kinematics(time_delta)

    def first_torque(self):
        g = GRAVITY
        num1 = -g * (2 * self.m1 + self.m2) * self.a1.sin()
        num2 = - self.m2 * g * (self.a1 - 2 * self.a2).sin()
        num3 = - 2 * (self.a1 - self.a2).sin() * self.m2
        num4 = self.a2.velocity ** 2 * self.l2 + self.a1.velocity ** 2 * self.l1 * (self.a1 - self.a2).cos()
        den = self.l1 * (2 * self.m1 + self.m2 - self.m2 * (2 * (self.a1 - self.a2)).cos())
        self.a1.add_torque((num1 + num2 + num3 * num4) / den)

    def second_torque(self):
        g = GRAVITY
        num1 = 2 * (self.a1 - self.a2).sin()
        num2 = self.a1.velocity ** 2 * self.l1 * (self.m1 + self.m2)
        num3 = g * (self.m1 + self.m2) * self.a1.cos()
        num4 = self.a2.velocity ** 2 * self.l2 * self.m2 * (self.a1 - self.a2).cos()
        den = self.l2 * (2 * self.m1 + self.m2 - self.m2 * (2 * (self.a1 - self.a2)).cos())
        self.a2.add_torque((num1 * (num2 + num3 + num4)) / den)

    # def update(self, control_dict):
    #     self.rect = self.get_rect()

    def draw(self):
        self.draw_pendulum()
        # self.draw_plot()

    def draw_pendulum(self):
        p2 = self.get_pendulum_position(self.origin, self.a1, self.l1)
        p3 = self.get_pendulum_position(p2, self.a2, self.l2)

        p1 = tuple(self.origin.__round__())
        p2 = tuple(p2.__round__())
        p3 = tuple(p3.__round__())
        #
        scrn = pygame_structures.Camera.screen
        #
        pg.draw.line(scrn, self.color, p1, p2, 1)
        pg.draw.line(scrn, self.color, p2, p3, 1)

        # pg.draw.circle(scrn, self.color, p2, self.m1)
        # pg.draw.circle(scrn, self.color, p3, self.m2)

    def draw_plot(self):
        p = Axis.plot(self.a1.angle, self.a2.angle, False, color=self.color)
        if hasattr(self, 'prv'):
            pg.draw.line(Axis.image, self.color, self.prv, p, 2)
        self.prv = p

def get_colors():
    width = 300 # Expected Width of generated Image
    height = 1 # Height of generated Image

    specratio = 255*6 / width

    red = 255
    green = 0
    blue = 0

    colors = []

    step = round(specratio)

    for u in range (0, height):
        for i in range (0, 255*6+1, step):
            if i > 0 and i <= 255:
                blue += step
            elif i > 255 and i <= 255*2:
                red -= step
            elif i > 255*2 and i <= 255*3:
                green += step
            elif i > 255*3 and i <= 255*4:
                blue -= step
            elif i > 255*4 and i <= 255*5:
                red += step
            elif i > 255*5 and i <= 255*6:
                green -= step

            colors.append((red, green, blue))
    return colors


def interpolate_colors(clr1, clr2, steps):
    lst = []

    dr = (clr2[0] - clr1[0]) / steps
    dg = (clr2[1] - clr1[1]) / steps
    db = (clr2[2] - clr1[2]) / steps
    for i in range(steps):
        lst.append(structures.add_tuples(clr1, structures.mul_tuple((dr, dg, db), i)))
        # print(structures.add_tuples((1, 1, 1), (3, 3, 3)))
    return lst


class Axis:
    W, H, clr, center, fnt, *_ = (None,) * 10
    image: pg.Surface = None

    @classmethod
    def plot(cls, x, y, draw=False, color=None):
        point = (cls.W * .5 + x * cls.W, cls.H * .5 + y * cls.H)
        if draw:
            pg.draw.circle(cls.image, color or cls.clr, point, 2)
        return point

    @classmethod
    def get_axis(cls, W, H):
        cls.H = H
        cls.W = W
        cls.image = pg.Surface((W, H), pg.SRCALPHA)
        cls.clr = pg.Color('white')
        cls.fnt = pg.font.SysFont('Robotic', 15)

        cls.center = (W//2, H//2)

        cls.draw_axis()
        cls.draw_graduation()
        return cls.image

    @classmethod
    def draw_axis(cls):
        pg.draw.line(cls.image, cls.clr, (0, cls.H//2), (cls.W, cls.H//2))
        pg.draw.line(cls.image, cls.clr, (cls.W//2, 0), (cls.W//2, cls.H))

    @classmethod
    def draw_graduation(cls):
        bound_x = 0.4
        bound_y = 0.4
        step_x = .1
        step_y = .1

        length = 20
        # horizontal
        n = round(bound_x / step_x)
        for i in range(-n, n + 1):
            value = i * step_x
            if abs(value) < 0.001:
                continue  # 0.0

            x_pos = value * cls.W
            pg.draw.line(cls.image, cls.clr,
                         cls.offset_center(x_pos, -length//2),
                         cls.offset_center(x_pos, length//2)
                         )

            text = cls.fnt.render(str(round(value, 4)), True, cls.clr)
            rect = text.get_rect()
            rect.center = cls.offset_center(x_pos, 0)
            rect.top = cls.offset_center(0, length)[1]

            cls.image.blit(text, rect)

        n = round(bound_y / step_y)
        for i in range(-n, n + 1):
            value = i * step_y
            if abs(value) < 0.001:
                continue  # 0.0

            y_pos = value * cls.H
            pg.draw.line(cls.image, cls.clr,
                         cls.offset_center(-length//2, y_pos),
                         cls.offset_center(length//2, y_pos)
                         )

            text = cls.fnt.render(str(round(value, 4)), True, cls.clr)
            rect = text.get_rect()
            rect.center = cls.offset_center(0, y_pos)
            rect.left = cls.offset_center(length, 0)[0]

            cls.image.blit(text, rect)

    @classmethod
    def offset_center(cls, x, y):
        val = structures.add_tuples((x, y), cls.center)
        # print(val)
        return val

def main():
    n = 1000
    # from colour import Color
    # red = Color('#FFFFFF')
    # clr = list(map(lambda rgb: (rgb[0] * 255, rgb[1] * 255, rgb[2] * 255),
    #                map(lambda x: x.rgb, red.range_to('#001E96', n))))

    clr = get_colors()
    # clr = interpolate_colors((180, 200, 255), (100, 30, 255), n)
    # print(clr)
    W = 1000
    H = 700
    screen = pygame_structures.DisplayMods.Windowed((W, H))
    # screen = pygame_structures.DisplayMods.FullScreen()
    W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height
    pygame_structures.Camera.init(screen, "static", None)
    pygame_structures.Camera.background = (0, 0, 0)
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame_structures.Map.No_Map()
    # axis = Axis.get_axis(W, H)
    # pygame_structures.Camera.blit_continuous_image(axis, (0, 0), float('inf'))
    # Axis.plot(.1, -.2, True)
    # print(screen.)
    # DoublePendulum((4 * W // 5, H//5), 0.3, 0.3, 100, 100, 10, 10, pg.Color('green'))
    # DoublePendulum((4 * W // 5, H//5), 0.3, 0.3, 100, 100, 10, 10, clr[0])
    for i in range(1, n):
        a = 3 * math.pi / 4 + i / 1000000
        # a = .05 + i / 1000
        DoublePendulum((W // 2, H//3), a, a, 100, 100, 10, 10, clr[int(i / n * len(clr))])
        # DoublePendulum((W // 2, H//3), a, a, 100, 100, 10, 10, clr[i])
    BaseSprite.collision_detection = False
    basic_loop()


if __name__ == '__main__':
    main()

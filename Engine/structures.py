from enum import Enum
import math
from numpy import sign
from pymaybe import maybe
from time import time


def print_time(func):
    def wrapper(*args, **kwargs):
        before = time()
        func(*args, **kwargs)
        print(time() - before)

    return wrapper


def get_run_time(func, *args, **kwargs):
    before = time()
    func(*args, **kwargs)
    return time() - before


def print_run_time(func, *args, **kwargs):
    before = time()
    val = func(*args, **kwargs)
    print(time() - before)
    return val


def get_all_subclasses(cls):
    all_subclasses = []
    for subclass in cls.__subclasses__():
        if subclass is type:
            continue
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def slope(point1, point2):
    return (point2[1] - point1[1]) / (point2[0] - point1[0])


def line(point1, point2):
    m = slope(point1, point2)
    b = point1[1] - point1[0] * m
    return f"y = {m}x {' + ' if b > 0 else ''}{b if round(b, 5) != 0.0 else ''}"


def angle_between_points(point1, point2):
    dy = point2[1] - point1[1]
    dx = point2[0] - point1[0]
    return DegTrigo.atan1(dx, dy)


def accurate_rect_collide_old(rect1, rect2, dpos1, dpos2=(0, 0)):
    rectangle_a = {"x1": rect1.x + dpos1[0], "y1": rect1.y + dpos1[1],
                   "x2": rect1.bottomright[0] + dpos1[0], "y2": rect1.bottomright[1] + dpos1[1]}
    rectangle_b = {"x1": rect2.x + dpos2[0], "y1": rect2.y + dpos2[1],
                   "x2": rect2.bottomright[0] + dpos2[0], "y2": rect2.bottomright[1] + dpos2[1]}

    return not ((rectangle_a["y1"] >= rectangle_b["y2"] or rectangle_a["x1"] >= rectangle_b["x2"]) or
                rectangle_a["x2"] <= rectangle_b["x1"] or rectangle_a["y2"] <= rectangle_b["y1"])


def add_tuples(*tuples):
    x, y = 0, 0
    for tup in tuples:
        x += tup[0]
        y += tup[1]
    return x, y


def get_rect_min_max(rect, dpos):
    return add_tuples(rect.topleft, dpos), \
           add_tuples(rect.bottomright, dpos)


def accurate_rect_collide(rect1, rect2, dpos1, dpos2=(0, 0)):
    max_1 = add_tuples(rect1.bottomright, dpos1)
    max_2 = add_tuples(rect2.bottomright, dpos2)
    min_1 = add_tuples(rect1.topleft, dpos1)
    min_2 = add_tuples(rect2.topleft, dpos2)
    if max_1[0] < min_2[0] or min_1[0] > max_2[0]:
        return False
    if max_1[1] < min_2[1] or min_1[1] > max_2[1]:
        return False
    return True


def sub_tuples(a, b):
    return a[0] - b[0], a[1] - b[1]


def mul_tuple(tup, num):
    return int(tup[0] * num), int(tup[1] * num)


class PrivateConstructorAccess(Exception):
    pass


class EmptyStackException(Exception):
    pass


class EmptyQueueException(Exception):
    pass


class VectorType(Enum):
    cartesian = 1
    polar = 2


class Direction:
    left = 0
    right = 1
    idle_right = 2
    idle_left = 3
    jumping_right = 4
    jumping_left = 5
    vertical = 6
    horizontal = 7

    idles = (idle_left, idle_right)
    lefts = (left, idle_left, jumping_left)
    rights = (right, idle_right, jumping_right)
    jumping = (jumping_left, jumping_right)


class DegTrigo:

    @staticmethod
    def deg_to_rad(deg):
        return math.radians(deg)

    @staticmethod
    def rad_to_deg(rad):
        return math.radians(rad)

    @staticmethod
    def atan(value):
        return math.degrees(math.atan(value))

    @classmethod
    def atan1(cls, x, y):  # 0 to 360
        if (x > 0) and (y >= 0):
            return cls.atan(y / x)
        elif (x > 0) and (y < 0):
            return cls.atan(y / x) + 360
        elif x < 0:
            return cls.atan(y / x) + 180
        elif (x == 0) and (y > 0):
            return 90
        elif (x == 0) and (y < 0):
            return 270
        return 0

    @classmethod
    def atan2(cls, x, y):  # -180 to 180
        if x > 0:
            return cls.atan(y / x)
        elif (x < 0) and (y >= 0):
            return cls.atan(y / x) + 180
        elif (x < 0) and (y < 0):
            return cls.atan(y / x) - 180
        elif (x == 0) and (y > 0):
            return 90
        elif (x == 0) and (y < 0):
            return -90
        return 0

    @staticmethod
    def asin(value):
        return math.degrees(math.asin(value))

    @staticmethod
    def acos(value):
        return math.degrees(math.acos(value))

    @staticmethod
    def sin(value):
        return math.sin(math.radians(value))

    @staticmethod
    def cos(value):
        return math.cos(math.radians(value))

    @staticmethod
    def tan(value):
        return math.tan(math.radians(value))


class Vector2:
    __key = object()

    def __init__(self, key, parm, vector_type):  # parm = (r, theta) or (x, y)
        if key is not self.__class__.__key:
            raise PrivateConstructorAccess(f"Access denied to private constructor of class {self.__class__}")
        if vector_type == VectorType.cartesian:
            self.x = parm[0]
            self.y = parm[1]
        elif vector_type == VectorType.polar:
            self.x = DegTrigo.cos(parm[1]) * parm[0]
            self.y = DegTrigo.sin(parm[1]) * parm[0]

    @property
    def r(self):
        return math.hypot(self.x, self.y)

    @r.setter
    def r(self, value):
        theta = self.theta
        self.x = DegTrigo.cos(theta) * value
        self.y = DegTrigo.sin(theta) * value

    @property
    def theta(self):
        return DegTrigo.atan1(self.x, self.y)

    @theta.setter
    def theta(self, value):
        r = self.r
        self.x = DegTrigo.cos(value) * r
        self.y = DegTrigo.sin(value) * r

    @property
    def values(self):
        return self.x, self.y

    @values.setter
    def values(self, value):
        self.x, self.y = value

    def magnitude(self):
        return abs(self.r)

    def square_magnitude(self):
        return self * self

    @classmethod
    def Cartesian(cls, x=0.0, y=0.0):
        return cls(cls.__key, (x, y), VectorType.cartesian)

    @classmethod
    def Point(cls, point):
        return cls(cls.__key, (point[0], point[1]), VectorType.cartesian)

    @classmethod
    def Polar(cls, r, theta):
        return cls(cls.__key, (r, theta), VectorType.polar)

    @classmethod
    def Zero(cls):
        return cls.Cartesian(0, 0)

    @classmethod
    def Copy(cls, vector):
        return cls.Cartesian(vector.x, vector.y)

    def copy(self):
        return Vector2.Copy(self)

    def reset(self):
        self.x = 0
        self.y = 0

    def rotate(self, angle):
        self.theta += angle

    def rotated(self, angle):
        new = self.copy()
        new.rotate(angle)
        return new

    def normalized(self):
        if not self:
            return Vector2.Zero()
        return Vector2.Cartesian(self.x / self.magnitude(), self.y / self.magnitude())

    def normalize(self):
        mag = self.magnitude()
        self.x /= mag
        self.y /= mag

    def sign(self):
        return Vector2.Cartesian(sign(self.x), sign(self.y))

    def normal(self):
        return Vector2.Cartesian(-self.y, self.x)

    def perpendicular(self):
        return self.normal()

    def tangent(self):
        return self.normal()

    def floor(self):
        return Vector2.Cartesian(int(self.x), int(self.y))

    def set_values(self, x=None, y=None):
        self.x = maybe(x).or_else(self.x)
        self.y = maybe(y).or_else(self.y)

    def __round__(self, n=None):
        return Vector2.Cartesian(round(self.x, n), round(self.y, n))

    def __neg__(self):
        return Vector2.Cartesian(-self.x, -self.y)

    def __pos__(self):
        return Vector2.Cartesian(self.x, self.y)

    def __add__(self, other):  # + operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            return self.__class__.Cartesian(self.x + other.x, self.y + other.y)
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot add a scalar to a vector")
        return NotImplemented

    def __iadd__(self, other):  # += operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            self.x += other.x
            self.y += other.y
            return self
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot add a scalar to a vector")
        return NotImplemented

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):  # - operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            return self.__class__.Cartesian(self.x - other.x, self.y - other.y)
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot subtract a scalar from a vector")
        return NotImplemented

    def __isub__(self, other):  # -= operator
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            self.x -= other.x
            self.y -= other.y
            return self
        elif isinstance(other, (int, float)):
            raise NotImplementedError("Cannot subtract a scalar from a vector")
        return NotImplemented

    def __rsub__(self, other):
        return self - other

    def __mul__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (int, float)):
            return Vector2.Cartesian(self.x * other, self.y * other)
        elif isinstance(other, self.__class__):
            "Returns the dot product of the vectors"
            return self.x * other.x + self.y * other.y
        return NotImplemented

    def __imul__(self, other):
        if isinstance(other, (int, float)):
            self.r *= other
            return self
        return NotImplemented

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (int, float)):
            return self.Cartesian(self.x / other, self.y / other)
        elif isinstance(other, self.__class__):
            "Returns the inverse of the dot product of the vectors"
            return self.x / other.x + self.y / other.y
        return NotImplemented

    def __itruediv__(self, other):
        if isinstance(other, (int, float)):
            self.x /= other
            self.y /= other
            return self
        return NotImplemented

    def __rtruediv__(self, other):
        return Vector2.Cartesian(other / self.x, other / self.y)

    def __floordiv__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (int, float)):
            self.Cartesian(self.x // other, self.y // other)
        elif isinstance(other, self.__class__):
            "Returns the inverse of the dot product of the vectors"
            return self.x // other.x + self.y // other.y
        return NotImplemented

    def __ifloordiv__(self, other):
        if isinstance(other, int):
            self.x //= other
            self.y //= other
            return self
        return NotImplemented

    def __rfloordiv__(self, other):
        return Vector2.Cartesian(other // self.x, other // self.y)

    def __str__(self, typ=None):
        if typ is None:
            typ = VectorType.cartesian
        if typ == VectorType.polar:
            return f"r={self.r:.2f}, θ={self.theta:.2f}"
        elif typ == VectorType.cartesian:
            return f"[{self.x:.5f}, {self.y:.5f}]"
        else:
            return f"r={self.r:.2f}, θ={self.theta:.2f}" + ' : ' f"[{self.x:.2f}, {self.y:.2f}]"

    def __repr__(self):
        return str(self)

    def __getitem__(self, item):
        if item in ('x', 0):
            return self.x
        elif item in ('y', 1):
            return self.y
        elif item == 'theta':
            return self.theta
        elif item == 'r':
            return self.r
        else:
            raise IndexError()

    def __setitem__(self, key, value):
        if not isinstance(value, (int, float)):
            raise AttributeError(f"Expected type 'int' or 'float', got '{type(value)}' instead")
        if key in ('x', 0):
            self.x = value
        elif key in ('y', 1):
            self.y = value
        elif key == 'theta':
            self.theta = value
        elif key == 'r':
            self.r = value
        else:
            raise IndexError()

    def __eq__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, self.__class__):
            return (self.x == other.x) and (self.y == other.y)
        return NotImplemented

    def __bool__(self):
        return bool(round(self.r, 5))

    def __pow__(self, other):
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        """returns the cross product of the vector self and other"""
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(other * self.y, -other * self.x)
        elif isinstance(other, Vector2):
            return self.x * other.y - self.y * other.x

    def __rpow__(self, other):
        """returns the cross product of other and the vector self"""
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(-other * self.y, other * self.x)
        elif isinstance(other, Vector2):
            return other ** self

    def __mod__(self, other):
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(self.x % other, self.y % other)

    def __abs__(self):
        return self.magnitude()

    def modf(self):
        x_float, x_num = math.modf(self.x)
        y_float, y_num = math.modf(self.y)
        return Vector2.Cartesian(x_float, y_float), \
            Vector2.Cartesian(x_num, y_num)


class Default:
    pass


class OrientedBoundingBox:
    def __init__(self, width_extent: Vector2, height_extent: Vector2):
        pass

    @classmethod
    def by_extent(cls, width_extent: Vector2, height_extent: Vector2):
        pass

    def by_size_and_orientation(self):
        pass


class IfCondition:
    def __init__(self, condition, reverse=False):
        self.reversed = reverse
        self.condition = condition

    def __bool__(self):
        return self.condition ^ self.reversed


class UntilCondition:
    conditions = []

    def __init__(self, condition, reverse=False):
        # self.state = bool(conddition()) ^ reverse
        self.state = False
        self.reversed = reverse
        self.condition = condition
        UntilCondition.conditions.append(self)

    def __bool__(self):
        return self.state

    @classmethod
    def update_all(cls):
        for cond in cls.conditions:
            if (not cond.state) and (bool(cond.condition()) ^ cond.reversed):
                cond.state = True
                cls.conditions.remove(cond)


class MovementStatus:
    idle = 0
    starting = 1
    moving = 2
    stopping = 3


class Queue:
    def __init__(self, *args):
        self.__items = []
        for i in args:
            self.insert(i)

    def insert(self, value):
        self.__items.append(value)

    def remove(self, default=None):
        if len(self.__items) > 0:
            return self.__items.pop(-1)
        elif default is None:
            raise EmptyQueueException("Can't remove an object from an empty queue")
        else:
            return default

    def head(self, default=None):
        if len(self.__items) > 0:
            return self.__items[-1]
        elif default is None:
            raise EmptyQueueException("Can't get the head of an empty queue")
        else:
            return default

    def __str__(self):
        return self.__items.reverse()

    def __bool__(self):
        return bool(self.__items)

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.__items)


class Stack:
    def __init__(self, *args):
        self.__items = []
        for arg in args:
            self.push(arg)

    def push(self, value):
        self.__items.append(value)

    def pop(self, default=None):
        if len(self.__items) > 0:
            return self.__items.pop()
        if default is None:
            raise EmptyStackException("Can't pop from an empty stack")
        return default

    def get_items(self):
        return self.__items

    def top(self, default=None):
        if len(self.__items) > 0:
            return self.__items[-1]
        if default is None:
            raise EmptyStackException("Can't read from an empty stack")
        return default

    def is_empty(self):
        return not bool(self)

    def __len__(self):
        return len(self.__items)

    def __str__(self):
        return str(self.__items)

    def __bool__(self):
        return bool(self.__items)


class Scroller:  # tested
    SCROLL_DELAY = 20  # the high it is the slower it takes to scroll to the player location

    def __init__(self, position, display_size, starting_position=None, delay=SCROLL_DELAY, minx=None, maxx=None,
                 miny=None, maxy=None):
        if isinstance(position, tuple):
            if len(position) == 2:
                self.position = lambda: position
        elif callable(position):
            self.position = position  # a function which returns the focus point
        else:
            raise AttributeError("Invalid position")
        # (to make it constant the function just need to be pure)
        self.display_size = display_size
        self.last_dx = 0  # not necessary, makes movement smoother
        self.last_dy = 0  # not necessary, makes movement smoother
        self.minx = maybe(minx).or_else(float("-inf"))
        self.maxx = maybe(maxx).or_else(float("inf"))
        self.miny = maybe(miny).or_else(float("-inf"))
        self.maxy = maybe(maxy).or_else(float("inf"))
        self.delay = delay

        if starting_position:
            self.tx, self.ty = starting_position
        else:
            self.__set_abs_position(self.position())

    def __str__(self):
        return f"({self.x}, {self.y})"

    @property
    def x(self):
        return int(self.tx)

    @property
    def y(self):
        return int(self.ty)

    @property
    def current_position(self):
        return self.x, self.y

    def __getitem__(self, item):
        if item in ('x', 0):
            return self.x
        elif item in ('y', 1):
            return self.y

    def __setitem__(self, k, value):
        if k in ('x', 0):
            self.tx = value
        elif k in ('y', 1):
            self.ty = value

    def __set_abs_position(self, position):
        x, y = position
        if x is None:
            x = self.position()[0]
        if y is None:
            y = self.position()[1]
        self.tx = min(max(x - self.display_size[0] / 2, self.minx), self.maxx)
        self.ty = min(max(y - self.display_size[1] / 2, self.miny), self.maxy)

    def set_position(self, position, smooth_move=False):
        if isinstance(position, tuple):
            if len(position) == 2:
                self.position = lambda: position
        elif callable(position):
            self.position = position  # a function which returns the focus point
        else:
            raise AttributeError("Invalid position")

        if not smooth_move:
            self.__set_abs_position(self.position())

    def __rsub__(self, other):
        return other[0] - self.x, other[1] - self.y

    def update(self):
        x, y = self.position()
        dx = (x - self.tx - self.display_size[0] / 2)
        if (abs(dx) < 3) and (abs(dx) < abs(self.last_dx)):  # makes movement smoother
            dx += sign(int(dx)) * Scroller.SCROLL_DELAY

        dy = (y - self.ty - self.display_size[1] / 2)
        if (abs(dy) < 3) and (abs(dy) < abs(self.last_dx)):  # makes movement smoother
            dy += sign(int(dy)) * Scroller.SCROLL_DELAY

        self.tx = min(max(self.tx + dx / Scroller.SCROLL_DELAY, self.minx), self.maxx)
        self.ty = min(max(self.ty + dy / Scroller.SCROLL_DELAY, self.miny), self.maxy)

        self.last_dx = dx
        self.last_dy = dy


members = [attr for attr in dir(Direction) if not callable(getattr(Direction, attr)) and not attr.startswith("__")]
direction = {eval(f'Direction.{i}'): i for i in members}

if __name__ == '__main__':
    v = Vector2.Cartesian(30, 30)
    v.normalize()

    print(v, v.magnitude())
    # A->velocity -= (1 / A->mass) * frictionImpulse
    # B->velocity += (1 / B->mass) * frictionImpulse


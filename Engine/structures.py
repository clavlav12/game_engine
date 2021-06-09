from enum import Enum
import math
from time import time, perf_counter


def maybe(value, or_else):
    """Return value if it isn't None. Else returns or else"""
    if value is None:
        return or_else
    else:
        return value


def sign(x):
    """Returns the sign of x"""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    return 0


def print_time(func):
    """Prints the time it takes for func to run each time it runs"""
    def wrapper(*args, **kwargs):
        before = perf_counter()
        func(*args, **kwargs)
        print(perf_counter() - before)
    return wrapper


def get_run_time(func, *args, **kwargs):
    """Returns the time it takes for func to run"""
    before = perf_counter()
    func(*args, **kwargs)
    return perf_counter() - before


def print_run_time(func, *args, **kwargs):
    """Prints the time it takes for func to run"""
    before = time()
    val = func(*args, **kwargs)
    print(time() - before)
    return val


def get_all_subclasses(cls):
    """Returns all the subclasses of cls"""
    all_subclasses = []
    for subclass in cls.__subclasses__():
        if subclass is type:
            continue
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def slope(point1, point2):
    """Returns the slope between two points"""
    return (point2[1] - point1[1]) / (point2[0] - point1[0])


def line(point1, point2):
    """Returns line equation by two points (y = mx + b)"""
    m = slope(point1, point2)
    b = point1[1] - point1[0] * m
    return f"y = {m}x {' + ' if b > 0 else ''}{b if round(b, 5) != 0.0 else ''}"


def angle_between_points(point1, point2):
    """Returns the angle two points make with the horizontal axis"""
    dy = point2[1] - point1[1]
    dx = point2[0] - point1[0]
    return DegTrigo.atan1(dx, dy)


def add_tuples(*tuples):
    """Adds tuples together like vectors"""
    lst = [0] * len(min(tuples, key=len))
    for i in range(len(lst)):
        for tup in tuples:
            lst[i] += tup[i]
    return tuple(lst)


def accurate_rect_collide(rect1, rect2, dpos1, dpos2=(0, 0)):
    """Checks for rect collision but accounts for float value"""
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
    """Subtracts tuples like 2D vector"""
    return a[0] - b[0], a[1] - b[1]


def mul_tuple(tup, num):
    """Multiply a tuple by a scalar like a vector"""
    return tuple(map(lambda x: x * num, tup))


class PrivateConstructorAccess(Exception):

    @classmethod
    def DefaultMessage(cls, class_):
        cls(f"Access denied to private constructor of class {class_}")


class EmptyStackException(Exception):
    pass


class EmptyQueueException(Exception):
    pass


class AlwaysSameValue:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        return self

    def __radd__(self, other):
        return self

    def __sub__(self, other):
        return self

    def __rsub__(self, other):
        return self

    def __and__(self, other):
        return self

    def __rand__(self, other):
        return self

    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self

    def __div__(self, other):
        return self

    def __rdiv__(self, other):
        return self

    def __divmod__(self, other):
        return self

    def __rdivmod__(self, other):
        return self

    def __int__(self):
        return int(self.value)

    def __bool__(self):
        return bool(self.value)

    def __str__(self):
        return str(self.value)


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
    up = 8
    down = 9

    idles = (idle_left, idle_right)
    lefts = (left, idle_left, jumping_left)
    rights = (right, idle_right, jumping_right)
    jumping = (jumping_left, jumping_right)


class DegTrigo:

    @staticmethod
    def deg_to_rad(deg):
        """Converts degrees to radians"""
        return math.radians(deg)

    @staticmethod
    def rad_to_deg(rad):
        """Converts radians to degrees"""
        return math.radians(rad)

    @staticmethod
    def atan(value):
        """Atan trigonometric function"""
        return math.degrees(math.atan(value))

    @classmethod
    def atan1(cls, x, y):  # 0 to 360
        """Atan1 trigonometric function"""
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
        """Atan2 trigonometric function"""
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
        """asin trigonometric function"""
        return math.degrees(math.asin(value))

    @staticmethod
    def acos(value):
        """acos trigonometric function"""
        return math.degrees(math.acos(value))

    @staticmethod
    def sin(value):
        """sin trigonometric function"""
        return math.sin(math.radians(value))

    @staticmethod
    def cos(value):
        """cos trigonometric function"""
        return math.cos(math.radians(value))

    @staticmethod
    def tan(value):
        """tan trigonometric function"""
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
        """Returns the size of the vector"""
        return abs(self.r)

    def square_magnitude(self):
        """Returns the square of the size of the vector (for fast comparison purposes)"""
        return self * self

    @classmethod
    def Cartesian(cls, x=0.0, y=0.0):
        """Creates a vector with cartesian coordinates"""
        return cls(cls.__key, (x, y), VectorType.cartesian)

    @classmethod
    def Point(cls, point):
        """Creates a vector from a tuple"""
        return cls(cls.__key, (point[0], point[1]), VectorType.cartesian)

    @classmethod
    def Polar(cls, r, theta):
        """Creates a vector with cartesian coordinates"""
        return cls(cls.__key, (r, theta), VectorType.polar)

    @classmethod
    def Unit(cls, angle):
        """Creates a unit vector by an angle"""
        return cls.Polar(1, angle)

    @classmethod
    def Zero(cls):
        """Returns the zero vector"""
        return cls.Cartesian(0, 0)

    @classmethod
    def Copy(cls, vector):
        """Returns a copy of vector"""
        return cls.Cartesian(vector.x, vector.y)

    def copy(self):
        """Returns a copy of self"""
        return Vector2.Copy(self)

    def reset(self):
        """Resets the vector"""
        self.x = 0
        self.y = 0

    def rotate(self, angle):
        """Rotates the vector by angle"""
        self.theta += angle

    def rotated(self, angle):
        """Returns a rotated version of the vector"""
        new = self.copy()
        new.rotate(angle)
        return new

    def normalized(self):
        """Returns a normalized version of self"""
        if not self:
            return Vector2.Zero()
        return Vector2.Cartesian(self.x / self.magnitude(), self.y / self.magnitude())

    def normalize(self):
        """Normalizes self"""
        mag = self.magnitude()
        self.x /= mag
        self.y /= mag

    def sign(self):
        """Return the vector changed by the sign operator"""
        return Vector2.Cartesian(sign(self.x), sign(self.y))

    def tangent(self):
        """Returns a vector tangent to self"""
        return Vector2.Cartesian(-self.y, self.x)

    def floor(self):
        """Return the vector changed by the floor operator"""
        return Vector2.Cartesian(int(self.x), int(self.y))

    def set_values(self, x=None, y=None):
        """Sets the x and y value of self"""
        self.x = maybe(x, self.x)
        self.y = maybe(y, self.y)

    def multiply_terms(self, other):
        """Multiply self by other by multiplying each term by the other"""
        return Vector2.Cartesian(self.x * other.x, self.y * other.y)

    def reversed(self, term):
        """Returns a version of self where term is reversed"""
        c = self.copy()
        c[term] *= -1
        return c

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
        return (-self) + other

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
            return self.Cartesian(self.x // other, self.y // other)
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

    def encode(self):
        """Encodes the vector so it can be send over a socket"""
        return f'{int(self.x)}:{int(self.y)}'

    def encode_polar(self):
        """Encodes the vector so it can be send over a socket, in a polar form (usfule for unit vectors)"""
        return f'{int(self.r)}:{int(self.theta)}'

    @classmethod
    def decode(cls, string):
        """Decodes the information encoded by Vector2.encode"""
        x, y = string.split(':')
        return cls.Cartesian(int(x), int(y))

    @classmethod
    def decode_polar(cls, string):
        """Decodes the information encoded by Vector2.decode_polar"""
        r, theta = string.split(':')
        return cls.Polar(int(r), int(theta))

    def str_polar(self):
        """same as __str__ but as a polar form"""
        return f"r={self.r:.2f}, θ={self.theta:.2f}"

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

    def __hash__(self):
        return hash((self.x, self.y))

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
        return NotImplemented

    def __rpow__(self, other):
        """returns the cross product of other and the vector self"""
        if isinstance(other, (list, tuple)) and len(other) >= 2:
            other = Vector2.Cartesian(other[0], other[1])
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(-other * self.y, other * self.x)
        elif isinstance(other, Vector2):
            return other ** self
        return NotImplemented

    def __mod__(self, other):
        if isinstance(other, (float, int)):
            return Vector2.Cartesian(self.x % other, self.y % other)
        return NotImplemented

    def __abs__(self):
        return self.magnitude()

    def __len__(self):
        return 2

    def modf(self):
        """Returns the float and the whole parts of the vector"""
        x_float, x_num = math.modf(self.x)
        y_float, y_num = math.modf(self.y)
        return Vector2.Cartesian(x_float, y_float), \
            Vector2.Cartesian(x_num, y_num)

    def min(self, other):
        """Returns the smallest terms from self and other"""
        other = Vector2.Point(other)
        return Vector2.Cartesian(
            min(self.x, other.x),
            min(self.y, other.y)
        )

    def max(self, other):
        """Returns the greatest terms from self and other"""
        other = Vector2.Point(other)
        return Vector2.Cartesian(
            max(self.x, other.x),
            max(self.y, other.y)
        )

    def add_point(self, point):
        """Adds a vector to a point"""
        return self + Vector2.Point(point)


class Default:
    pass


class UntilCondition:
    """A condition that stays the same until a requirement is made"""
    conditions = []

    def __init__(self, condition, reverse=False):
        self.state = False
        self.reversed = reverse
        self.condition = condition
        UntilCondition.conditions.append(self)

    def __bool__(self):
        return self.state

    @classmethod
    def update_all(cls):
        """Called each frame. updates all conditions"""
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
        """Inserts a value to the queue"""
        self.__items.append(value)

    def remove(self, default=None):
        """Removes a value from the queue"""
        if len(self.__items) > 0:
            return self.__items.pop(-1)
        elif default is None:
            raise EmptyQueueException("Can't remove an object from an empty queue")
        else:
            return default

    def head(self, default=None):
        """Returns the head of the queue"""
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
        """Push a value to the stack"""
        self.__items.append(value)

    def pop(self, default=None):
        """Pops a value from the stack"""
        if len(self.__items) > 0:
            return self.__items.pop()
        if default is None:
            raise EmptyStackException("Can't pop from an empty stack")
        return default

    def get_items(self):
        """Returns the stack as a list of items"""
        return self.__items

    def top(self, default=None):
        """Returns the top of the stack without popping it"""
        if len(self.__items) > 0:
            return self.__items[-1]
        if default is None:
            raise EmptyStackException("Can't read from an empty stack")
        return default

    def is_empty(self):
        """Returns whether or not the stack is empty"""
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
        self.minx = maybe(minx, float("-inf"))
        self.maxx = maybe(maxx, float("inf"))
        self.miny = maybe(miny, float("-inf"))
        self.maxy = maybe(maxy, float("inf"))
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
        """Sets the position without a smooth transition"""
        x, y = position
        self.tx = min(max(x - self.display_size[0] / 2, self.minx), self.maxx)
        self.ty = min(max(y - self.display_size[1] / 2, self.miny), self.maxy)

    def set_position(self, position, smooth_move=False):
        """Sets the position of the scroller to position. For a smooth transition, pass smooth_move=True."""
        if isinstance(position, tuple):
            if len(position) == 2:
                self.position = lambda: position
        elif callable(position):
            self.position = position  # a function which returns the focus point
        else:
            raise AttributeError("Invalid position")

        if not smooth_move:  # for a smooth transition just wait
            self.__set_abs_position(self.position())

    def __rsub__(self, other):
        return other[0] - self.x, other[1] - self.y

    def update(self):
        """Updates the scroller, called each frame"""
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


class Layer:
    num_of_layers = 1

    def __init__(self, *exceptions):
        """
        :param exceptions: Layers to exclude the object from
        """
        all_layers = 2 ** self.num_of_layers - 1  # Σ(2^(x - 1)) from x=0 to n = 2^n - 1

        for exception in exceptions:
            all_layers ^= 2 ** (exception - 1)

        self.layers = all_layers

    @classmethod
    def add_layer(cls):
        """Adds a collision layer"""
        cls.num_of_layers += 1

    def __and__(self, other):
        if isinstance(other, Layer):
            return self.layers & other.layers
        return NotImplemented


if __name__ == '__main__':
    v = Vector2.Cartesian(30, 30)
    v.normalize()

    # print(v, v.magnitude())
    # A->velocity -= (1 / A->mass) * frictionImpulse
    # B->velocity += (1 / B->mass) * frictionImpulse


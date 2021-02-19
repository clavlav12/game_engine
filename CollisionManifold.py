from Engine.structures import Vector2
import Bodies
import math
from Engine.Debug import *
from Engine.pygame_structures import Camera
BaseSprite: type
RigidBody: type
Tile: type


def initialize(BaseSprite_, RigidBody_, Tile_):
    global BaseSprite, RigidBody, Tile
    BaseSprite = BaseSprite_
    RigidBody = RigidBody_
    Tile = Tile_


class CollidedSprite:
    def __init__(self, obj, inv_mass, inv_moment_of_inertia, position, velocity, angular_velocity, elasticity):
        self.angular_velocity = angular_velocity
        self.velocity = velocity
        self.position = position
        self.inv_moment_of_inertia = inv_moment_of_inertia
        self.inv_mass = inv_mass
        self.obj = obj
        self.elasticity = elasticity

    @classmethod
    def Create(cls, obj):
        if isinstance(obj, RigidBody):
            return cls.from_rigid_body(obj)
        elif isinstance(obj, BaseSprite):
            return cls.from_regular_sprite(obj)
        elif isinstance(obj, pygame_structures.TileCollection):
            return cls.from_tile_collection(obj)

    @classmethod
    def from_tile_collection(cls, collection):
        return cls(collection.reference, 0, 0, Vector2.Point(collection.reference.rect.center), Vector2.Zero(), 0,
                   collection.reference.elasticity)

    @classmethod
    def from_regular_sprite(cls, sprite):
        return cls(sprite, 1/sprite.mass, 0, sprite.position, sprite.velocity, 0, sprite.elasticity)

    @classmethod
    def from_rigid_body(cls, sprite):
        return cls(sprite, 1/sprite.mass, 1/sprite.moment_of_inertia, sprite.position,
                   sprite.velocity, sprite.angular_velocity, sprite.elasticity)

    def add_to_position(self, displacement):
        if isinstance(self.obj, BaseSprite):
            self.obj.position += displacement
            self.obj.set_position()

    def apply_impulse(self, impulse_vector: Vector2, arm: Vector2 = None):
        if isinstance(self.obj, BaseSprite):
            self.obj.velocity += impulse_vector * self.obj.inv_mass
        if isinstance(self.obj, RigidBody) and arm is not None:
            self.obj.angular_velocity += math.degrees(
                self.obj.inv_moment_of_inertia * (arm ** impulse_vector)
            )


class CollisionManifold:
    Manifolds = []

    def __init__(self, contact_point, normal, depth, obj1, obj2, collision=True, *, solve=True):
        self.contact_point = contact_point
        self.normal = normal
        self.depth = depth
        self.collision = collision
        self.obj1 = obj1
        self.obj2 = obj2

        if solve and collision:
            self.add_manifold(self)

    @classmethod
    def NoCollision(cls):
        return cls(None, None, 0, None, None, False)

    def __bool__(self):
        return self.collision

    def penetration_resolution(self):
        first = CollidedSprite.Create(self.obj1)
        second = CollidedSprite.Create(self.obj2)
        if (not self.depth) or not (first.inv_mass + second.inv_mass):
            return

        # pen_res = self.normal * self.depth / (first.inv_mass + second.inv_mass)

        percent = .2
        slop = .1
        pen_res = max(self.depth - slop, 0.0) / (first.inv_mass + second.inv_mass) * percent * self.normal
        # print(max(self.depth - slop, 0.0))
        first.add_to_position(pen_res * first.inv_mass)
        second.add_to_position(-pen_res * second.inv_mass)

    def collision_response(self):
        first = CollidedSprite.Create(self.obj1)
        second = CollidedSprite.Create(self.obj2)

        # closing velocities
        if self.contact_point is not None:
            arm1 = self.contact_point - first.position
        else:
            arm1 = Vector2.Zero()
        rot_vel1 = math.radians(first.angular_velocity) ** arm1
        close_vel1 = first.velocity + rot_vel1

        if self.contact_point is not None:
            arm2 = self.contact_point - second.position
        else:
            arm2 = Vector2.Zero()

        rot_vel2 = math.radians(second.angular_velocity) ** arm2
        close_vel2 = second.velocity + rot_vel2

        # impulse augmentation
        imp_aug1 = arm1 ** self.normal
        imp_aug1 = imp_aug1 * first.inv_moment_of_inertia * imp_aug1
        imp_aug2 = arm2 ** self.normal
        imp_aug2 = imp_aug2 * second.inv_moment_of_inertia * imp_aug2

        relative_velocity = close_vel1 - close_vel2
        separating_velocity = relative_velocity * self.normal
        
        if separating_velocity > 0:
            return

        # new_separating_velocity = - separating_velocity * min(obj1.elasticity, obj2.elasticity)
        #
        # vel_sep_diff = new_separating_velocity - separating_velocity

        if not (first.inv_mass + second.inv_mass + imp_aug1 + imp_aug2):
            return

        beta = 0

        b = beta * self.depth
        impulse = (-separating_velocity * (min(first.elasticity, second.elasticity) + 1) + b) / (
                first.inv_mass + second.inv_mass + imp_aug1 + imp_aug2)

        # if impulse < 1000000:
        #     impulse = -separating_velocity/ (
        #             obj1.inv_mass + obj2.inv_mass + imp_aug1 + imp_aug2)

        impulse_vector = self.normal * impulse
        first.apply_impulse(impulse_vector, arm1)
        second.apply_impulse(-impulse_vector, arm2)
        self.original_friction(first, second, impulse)

    def original_friction(self, first, second, j):
        obj1: RigidBody
        obj2: RigidBody

        if self.contact_point is not None:
            arm1 = self.contact_point - first.position
        else:
            arm1 = first.position
        rot_vel1 = math.radians(first.angular_velocity) ** arm1
        close_vel1 = first.velocity + rot_vel1

        if self.contact_point is not None:
            arm2 = self.contact_point - second.position
        else:
            arm2 = second.position

        rot_vel2 = math.radians(second.angular_velocity) ** arm2
        close_vel2 = second.velocity + rot_vel2

        # impulse augmentation
        imp_aug1 = arm1 ** self.normal
        imp_aug1 = imp_aug1 * first.inv_moment_of_inertia * imp_aug1
        imp_aug2 = arm2 ** self.normal
        imp_aug2 = imp_aug2 * second.inv_moment_of_inertia * imp_aug2

        rv = second.velocity - first.velocity
        rv = close_vel1 - close_vel2

        normal = self.normal

        t = rv - (normal * (rv * normal))
        if not t.square_magnitude():
            return

        t.normalize()
        jt = -rv * t
        # if abs(jt) < 70:
        #     return
        jt /= (first.inv_mass + second.inv_mass + imp_aug1 + imp_aug2)

        # if abs(jt) < 100_000:
        #     return

        sf = df = .2

        if abs(jt) < j * sf:
            tangentImpulse = t * jt
        else:
            tangentImpulse = t * -j * df

        first.apply_impulse(tangentImpulse, arm1)
        second.apply_impulse(-tangentImpulse, arm2)

    @classmethod
    def clear(cls):
        cls.Manifolds.clear()

    @classmethod
    def add_manifold(cls, manifold):
        cls.Manifolds.append(manifold)


class ManifoldGenerator:
    def __init__(self, function, complexity: float):
        """
        :param function: a function that takes two sprites and generate a collision manifold
        :param complexity:  how complex the function is (in case two sprites want different manifolds,
         the more complex one will be used)
        """
        self.func = function
        self.complexity = complexity

    def __and__(self, other):
        if isinstance(other, ManifoldGenerator):
            return max(self, other, key=lambda x: x.complexity)
        return NotImplemented

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

from Engine.structures import Vector2
from Engine.Debug import *
BaseSprite: type
RigidBody: type
Tile: type


def initialize(BaseSprite_, RigidBody_, Tile_):
    """
    Used to avoid recursive importing
    :param BaseSprite_: BaseSprite class (from base_sprites.py)
    :param RigidBody_:  RigidBody class (from base_sprites.py)
    :param Tile_:  Tile class (from base_sprites.py)
    """
    global BaseSprite, RigidBody, Tile
    BaseSprite = BaseSprite_
    RigidBody = RigidBody_
    Tile = Tile_


class CollidedSprite:
    def __init__(self, obj, inv_mass, inv_moment_of_inertia, position, velocity, angular_velocity, restitution,
                 static_friction, dynamic_friction):
        self.angular_velocity = angular_velocity
        self.velocity = velocity
        self.position = position
        self.inv_moment_of_inertia = inv_moment_of_inertia
        self.inv_mass = inv_mass
        self.obj = obj
        self.restitution = restitution
        self.static_friction = static_friction
        self.dynamic_friction = dynamic_friction

    @classmethod
    def Create(cls, obj):
        """
        Generates CollidedSprite by object type
        """
        if isinstance(obj, RigidBody):
            return cls.from_rigid_body(obj)
        elif isinstance(obj, BaseSprite):
            return cls.from_regular_sprite(obj)
        elif isinstance(obj, pygame_structures.TileCollection):
            return cls.from_tile_collection(obj)

    @classmethod
    def from_tile_collection(cls, collection):
        """
        Generates CollidedSprite by TileCollection
        """
        return cls(collection.reference, 0, 0, Vector2.Point(collection.reference.rect.center), Vector2.Zero(), 0,
                   collection.reference.restitution, collection.reference.static_friction,
                   collection.reference.dynamic_friction)

    @classmethod
    def from_regular_sprite(cls, sprite):
        """
        Generates CollidedSprite by BaseSprite
        """
        return cls(sprite, 1/sprite.mass, 0, sprite.position, sprite.velocity, 0, sprite.restitution,
                   sprite.static_friction, sprite.dynamic_friction)

    @classmethod
    def from_rigid_body(cls, sprite):
        """
        Generates CollidedSprite by RigidBody
        """
        return cls(sprite, 1/sprite.mass, 1/sprite.moment_of_inertia, sprite.position,
                   sprite.velocity, sprite.angular_velocity, sprite.restitution, sprite.static_friction, sprite.dynamic_friction)

    def add_to_position(self, displacement):
        """
        Moves movable sprites by displacement (Vector2)
        """
        if isinstance(self.obj, BaseSprite):
            self.obj.position += displacement
            self.obj.set_position()

    def apply_impulse(self, impulse_vector: Vector2, arm: Vector2 = None):
        """
        Applies impulse if relevant
        :param impulse_vector: Vector of the impulse
        :param arm: Vector from com to contact point (only relevant for RigidBodies)
        """
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
        self.depth = depth + .2
        self.collision = collision
        self.obj1 = obj1
        self.obj2 = obj2
        if solve and collision:
            self.add_manifold(self)

    def __str__(self):
        if self.collision:
            return f"CollisionManifold(cp={self.contact_point}, n={self.normal}, d={self.depth})"
        else:
            return f"CollisionManifold(None)"

    @classmethod
    def NoCollision(cls):
        """
        Generates empty CollisionManifold that is not solved
        """
        return cls(None, None, 0, None, None, False)

    def __bool__(self):
        """
        :return: Whether or not a collision happened
        """
        return self.collision

    def penetration_resolution(self):
        """
        Solves penetration
        """
        first = CollidedSprite.Create(self.obj1)
        second = CollidedSprite.Create(self.obj2)
        if (not self.depth) or not (first.inv_mass + second.inv_mass):
            return

        percent = .2
        slop = .1
        pen_res = max(self.depth - slop, 0.0) / (first.inv_mass + second.inv_mass) * percent * self.normal
        first.add_to_position(pen_res * first.inv_mass)
        second.add_to_position(-pen_res * second.inv_mass)

    def collision_response(self):
        """
        Velocity response + friction
        """
        first = CollidedSprite.Create(self.obj1)
        second = CollidedSprite.Create(self.obj2)

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

        if not (first.inv_mass + second.inv_mass + imp_aug1 + imp_aug2):
            return

        beta = 0

        b = beta * self.depth
        impulse = (-separating_velocity * (max(first.restitution, second.restitution) + 1) + b) / (
                first.inv_mass + second.inv_mass + imp_aug1 + imp_aug2)

        impulse_vector = self.normal * impulse
        first.apply_impulse(impulse_vector, arm1)
        second.apply_impulse(-impulse_vector, arm2)
        self.apply_friction(first, second, impulse)

    def apply_friction(self, first, second, j):
        """
        Applies friction
        :param first: first CollidedSprite
        :param second: second CollidedSprite
        :param j: Impulse vector
        """
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

        rv = close_vel1 - close_vel2

        normal = self.normal

        t = rv - (normal * (rv * normal))
        if not t.square_magnitude():
            return

        t.normalize()
        jt = -rv * t
        jt /= (first.inv_mass + second.inv_mass + imp_aug1 + imp_aug2)

        sf = math.hypot(first.static_friction, second.static_friction)
        df = math.hypot(first.dynamic_friction, second.dynamic_friction)

        if abs(jt) < j * sf:
            tangentImpulse = t * jt
        else:
            tangentImpulse = t * -j * df

        first.apply_impulse(tangentImpulse, arm1)
        second.apply_impulse(-tangentImpulse, arm2)

    @classmethod
    def clear(cls):
        """
        Clears not solved manifolds
        """
        cls.Manifolds.clear()

    @classmethod
    def add_manifold(cls, manifold):
        """
        Adds a manifold to solve
        """
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
        """
        Combines two ManifoldGenerator by taking the more complex one
        :param other: another ManifoldGenerator
        :return: the more complex ManifoldGenerator
        """
        if isinstance(other, ManifoldGenerator):
            return max(self, other, key=lambda x: x.complexity)
        return NotImplemented

    def __call__(self, *args, **kwargs):
        """
        Calls generator
        """
        return self.func(*args, **kwargs)

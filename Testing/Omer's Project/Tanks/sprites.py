import Engine.base_control as base_controls
import Engine.base_sprites as base_sprites
import Engine.pygame_structures as pygame_structures
import Engine.structures as structures
import Engine.Sound as Sound
import Engine.Particle as Particle
import pygame
from Engine.Debug import draw_circle, draw_arrow
import math
from enum import Enum
from bisect import bisect_left

pg = pygame
Direction = structures.Direction
Vector2 = structures.Vector2


class MissileMagazine(pygame.sprite.Group):
    magazines_list = []

    def __init__(self, shot_delay, capacity, tank, damage=base_sprites.GunBullet.DAMAGE):
        super(MissileMagazine, self).__init__()
        self.capacity = capacity
        self.shot_timer = pygame_structures.Timer(shot_delay)
        self.damage = damage
        self.tank = tank
        base_sprites.Magazine.magazines_list.append(self)

    def add_bullet(self, direction, speed, offset=(0, 0), position_from_tale=False):
        if self.shot_timer.finished() and not self.full():
            self.shot_timer.activate()
            bull = Missile(direction.theta, self.tank, speed, offset, position_from_tale)
            self.add(bull)
            return bull
        return None

    def full(self):
        return len(self) >= self.capacity


class TankShootControl(base_controls.BaseControl):
    MAG_CAPACITY = 1
    MAG_CAPACITY = 10000
    SHOT_DELAY = 1
    # SHOOT_SPEED = 1000
    SHOOT_SPEED = 1500

    def __init__(self, direction, sprite, mag_capacity=MAG_CAPACITY, shot_delay=SHOT_DELAY):
        self.magazine = MissileMagazine(shot_delay, mag_capacity, sprite)
        base_controls.BaseControl.__init__(self, sprite, direction)

    def shoot(self, direction, speed, offset=(0, 0), position_from_tale=False):
        # final_vector = Vector2.Copy(velocity_vector)
        # final_vector.x += self.sprite.velocity.x
        b = self.magazine.add_bullet(direction, speed, offset, position_from_tale)
        if b is not None:
            """play sound!"""
            pass
            # MySprites.player.play_sound(Sounds.gun_shot)


class TankControl(base_controls.BetterAllDirectionMovement, TankShootControl):
    MOVING_SPEED = 350  # p/s
    SHOOTING_SPEED = 800  # p/s
    ROTATION_SPEED = 180  # degrees / s
    SHOT_DELAY = 0.4
    TURRET_DELAY = 0.01

    def __init__(self, up_key, down_key, left_key, right_key, clockwise_key, counter_clockwise_key,
                 shoot_key,
                 tank, init_direction):
        base_controls.BetterAllDirectionMovement.__init__(self, tank, up_key, down_key, left_key, right_key,
                                                          self.MOVING_SPEED, init_direction)
        TankShootControl.__init__(self, init_direction, tank)
        self.shoot_key = shoot_key
        self.right_key = right_key
        self.left_key = left_key
        self.clockwise_key = clockwise_key
        self.counter_clockwise_key = counter_clockwise_key
        self.turret_move_timer = pygame_structures.Timer(TankControl.TURRET_DELAY)

    def reset(self):
        base_controls.BaseControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        pressed_keys = kwargs['keys']
        base_controls.BetterAllDirectionMovement.move(self, **kwargs)

        if pressed_keys[self.shoot_key]:
            r = Turret.TURRET_IMAGE_SIZE[1] * 1.5 - Turret.center_offset[1]
            a = - 90 - self.sprite.turret.orientation

            self.shoot(Vector2.Polar(1, self.sprite.turret.orientation + 90), self.SHOOTING_SPEED,
                       tuple(Vector2.Polar(r, a)), True
                       )


class TurretControl(base_controls.BaseControl):
    def __init__(self, sprite: base_sprites.BaseRigidBody, roll_cw, roll_ccw, turning_speed):
        super(TurretControl, self).__init__(sprite, structures.Direction.idle_left)

        self.turning_speed = turning_speed
        self.cw_key = roll_cw
        self.ccw_key = roll_ccw

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        super(TurretControl, self).move(**kwargs)
        keys = kwargs['keys']

        if keys[self.cw_key]:
            self.sprite.angular_velocity = self.turning_speed
        elif keys[self.ccw_key]:
            self.sprite.angular_velocity = -self.turning_speed
        else:
            self.sprite.angular_velocity = 0


def sign(a):
    if a > 0:
        return 1
    elif a < 0:
        return -1
    return 0


class Color(Enum):
    black = 0
    green = 1


class Turret(base_sprites.ImagedRigidBody):
    TURRET_IMAGE = {
        0: pygame.image.load('Arts/army_tank_turret_black.png'),
        1: pygame.image.load('Arts/army_tank_turret.png'),
    }

    scale = 1

    for color in TURRET_IMAGE:
        TURRET_IMAGE[color] = pygame_structures.smooth_scale_image(TURRET_IMAGE[color], scale)

    TURNING_SPEED = 180
    TURRET_IMAGE_SIZE = TURRET_IMAGE[0].get_size()
    center_offset = tuple(Vector2.Point(TURRET_IMAGE_SIZE)/2 + (0, 20))

    manifold_generator = lambda _, __: None
    manifold_generator = base_sprites.ManifoldGenerator(manifold_generator, float('inf'))

    def __init__(
            self,
            control: base_controls.controls,
            color: Color,
            center,
            orientation
    ):
        self.color = color
        img = self.TURRET_IMAGE[self.color.value]

        super(Turret, self).__init__(
            img,
            img.get_rect(center=center),
            50,
            50,
            orientation,
            TurretControl(self, control.cw, control.ccw, self.TURNING_SPEED),
            self.center_offset
        )
        self.collider.manifold_generator = self.manifold_generator
        self.collide_check_by_rect = True


class Tank(base_sprites.AdvancedSprite):
    TANK_IMAGE = {
        0: pygame.image.load('Arts/army_tank_body_black.png'),
        1: pygame.image.load('Arts/army_tank_body.png'),
    }

    scale = 1

    for color in TANK_IMAGE:
        TANK_IMAGE[color] = pygame_structures.smooth_scale_image(TANK_IMAGE[color], scale)

    HIT_POINTS = 2000
    turret_offset = structures.Vector2.Cartesian(10, 0)
    turret_offset = structures.Vector2.Zero()

    possible_angles = [0, 45, 90, 135, 180, 225, 270, 315, 360]

    def __init__(self,
                 init_direction,
                 position,
                 control_keys: base_controls.controls,
                 shoot_key,
                 color: Color,
                 health_bar_color=None
                 ):
        self.sprite_collision_check_by_rect = True
        self.collide_check_by_rect = True

        angle = structures.Vector2.Point(init_direction).theta
        base_image = self.TANK_IMAGE[color.value]
        self.rotatable_image = pygame_structures.RotatableImage(base_image, angle - 90, (0, 0))
        control = TankControl(*control_keys, shoot_key, self, structures.Direction.left)
        super(Tank, self).__init__(
            self.rotatable_image.edited_img.get_rect(center=position),
            control,
            50,
            self.HIT_POINTS,
            health_bar_color
        )

        self.current_angle = angle - 90
        self.turret = Turret(control_keys, color, self.get_turret_position(), self.current_angle - 180)

        print(self.health_bar.bar_width, self.health_bar.bar_height)

    def get_turret_position(self):
        return structures.add_tuples(self.rect.center,
                                     self.turret_offset.multiply_terms(Vector2.Polar(1, self.current_angle)))

    def update(self, _):
        if self.control.moving_direction:
            self.current_angle = self.control.moving_direction.reversed(1).theta + 90
            self.rotatable_image.rotate(self.current_angle)
    # def apply_gravity(self):
    #     pass

    @classmethod
    def closest_angle(cls, myNumber):
        """
        Returns closest angle to myNumber.

        If two numbers are equally close, return the smallest number.
        """
        pos = bisect_left(cls.possible_angles, myNumber)
        if pos == 0:
            return cls.possible_angles[0]
        if pos == len(cls.possible_angles):
            return cls.possible_angles[-1]
        before = cls.possible_angles[pos - 1]
        after = cls.possible_angles[pos]
        if after - myNumber < myNumber - before:
            return after
        else:
            return before

    def draw(self, draw_health=True):
        if self.hit_points > 0:
            self.image, _ = self.rotatable_image.blit_image(self.position, False)
            self.rect.size = self.image.get_size()
            super(Tank, self).draw(draw_health)
            # self.draw_rect()

    def update_position(self, time_delta):
        super(Tank, self).update_position(time_delta)
        self.turret.set_position(*self.get_turret_position())

    def set_position(self, x=None, y=None):
        super(Tank, self).set_position(x, y)
        self.turret.set_position(*self.get_turret_position())

    def apply_gravity(self):
        pass

    def die(self):
        self.turret.kill()
        self.kill()


class Missile(base_sprites.Bullet):
    DAMAGE = 100
    EXPLOSION_DAMAGE = 2

    TRAVEL_DISTANCE = 1000
    MISSILE_IMAGE = pygame.image.load(r'images/missile.png').convert_alpha()
    MISSILE_IMAGE = pygame_structures.smooth_scale_image(MISSILE_IMAGE, 1)

    def __init__(self, angle, tank: Tank, initial_speed, offset=(0, 0), position_from_tale=False):
        image = pg.transform.rotate(self.MISSILE_IMAGE, angle)

        if not position_from_tale:
            r = Missile.MISSILE_IMAGE.get_rect(center=structures.add_tuples(tank.rect.center, offset))
        else:
            # r = Turret.TURRET_IMAGE_SIZE[1] * 1.5 - Turret.center_offset[1]
            # a = - 90 - self.turret.orientation
            o = Vector2.Polar(
                Missile.MISSILE_IMAGE.get_height() / 2, -angle
            )

            r = Missile.MISSILE_IMAGE.get_rect(center=structures.add_tuples(tank.rect.center, offset, o
                                                                            ))

        super(Missile, self).__init__(r, Missile.DAMAGE, Missile.TRAVEL_DISTANCE)
        self.image = image
        self.killed = False
        self.rect_collision = False
        self.velocity += Vector2.Polar(initial_speed, -angle) #+ tank.velocity
        self.angle = angle
        self.shooters = [tank, tank.turret]

        self.sprite_collision_check_by_rect = False
        self.collide_check_by_rect = True

    def kill(self):
        if not self.killed:
            pygame_structures.Camera.shake()
            base_sprites.player.play_sound(Sound.Sounds.explosion)
            pygame_structures.Camera.add_particle(Particle.Explosion, self.rect.center,
                                                  collide_function=self.explosion_collide)
            super(Missile, self).kill()
            self.killed = True

    def explosion_collide(self, other):
        if isinstance(other, base_sprites.AdvancedSprite) and not other.is_dead:
            if other.resistance_timer.finished():
                other.hit_points -= self.EXPLOSION_DAMAGE
                other.resistance_timer.activate()

    def collision(self, other):
        if (isinstance(other, base_sprites.AdvancedSprite)) and (not other.is_dead) and (other not in self.shooters):
            if other.resistance_timer.finished():
                other.hit_points -= self.damage
                other.resistance_timer.activate()
            self.kill()
            return False
        elif isinstance(other, base_sprites.Bullet):
            self.kill()
            return False

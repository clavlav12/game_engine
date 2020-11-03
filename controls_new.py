from structures import Vector2, Direction
from Sound import Sounds
import MySprites
from numpy import sign
from pymaybe import maybe
import pygame

class BaseControl:
    def __init__(self, _sprite, _direction):
        self.sprite = _sprite
        self.direction = _direction
        self.in_control = True

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        pass

    def sprite_collide(self, sprite):
        pass

    def platform_collide(self, direction, platform):
        pass

    def reset(self):
        if self.direction in Direction.lefts:
            self.direction = Direction.idle_left
        elif self.direction in Direction.rights:
            self.direction = Direction.idle_right


class ShootControl(BaseControl):
    MAG_CAPACITY = 4

    def __init__(self, direction, sprite, mag_capacity=MAG_CAPACITY, color="yellow", size='large', shot_delay=0.0):
        self.magazine = MySprites.Magazine(color, size, shot_delay, mag_capacity)
        BaseControl.__init__(self, sprite, direction)

    def shoot(self, velocity_vector):
        final_vector = Vector2.Copy(velocity_vector)
        final_vector.x += self.sprite.velocity.x

        if self.direction in Direction.rights:
            b = self.magazine.add_bullet(self.sprite.rect.right + 5, self.sprite.rect.center[1], final_vector)
        else:
            size = MySprites.GunBullet.get_image_size(self.magazine.color, self.magazine.size)
            b = self.magazine.add_bullet(self.sprite.rect.left - size[0] - 5, self.sprite.rect.center[1], final_vector)
        if b is not None:
            MySprites.player.play_sound(Sounds.gun_shot)


class TankShootControl(BaseControl):
    MAG_CAPACITY = 1
    SHOT_DELAY = 1
    # SHOOT_SPEED = 1000
    SHOOT_SPEED = 1500

    def __init__(self, direction, sprite, mag_capacity=MAG_CAPACITY, shot_delay=SHOT_DELAY):
        self.magazine = MySprites.MissileMagazine(shot_delay, mag_capacity, sprite)
        BaseControl.__init__(self, sprite, direction)

    def shoot(self, velocity_vector):
        # final_vector = Vector2.Copy(velocity_vector)
        # final_vector.x += self.sprite.velocity.x
        b = self.magazine.add_bullet(velocity_vector)
        if b is not None:
            """play sound!"""
            pass
            # MySprites.player.play_sound(Sounds.gun_shot)


class LeftRightMovement(BaseControl):
    def __init__(self, moving_speed, sprite, direction):
        self.moving_speed = moving_speed
        super(LeftRightMovement, self).__init__(sprite, direction)

    def can_move(self):
        return True
        # return (not hasattr(self.sprite, 'on_platform') or bool(self.sprite.on_platform)) or (
        #         isinstance(self, JumpControl) and self.jumping)

    def move(self, **kwargs):
        if self.direction == Direction.right and self.can_move():
            self.sprite.add_force(Vector2.Cartesian((self.moving_speed - self.sprite.velocity.x) * self.sprite.mass),
                                  'walking')
        elif self.direction == Direction.left and self.can_move():  # moving left
            self.sprite.add_force(Vector2.Cartesian((-self.sprite.velocity.x - self.moving_speed) * self.sprite.mass),
                                  'walking')
        super(LeftRightMovement, self).move(**kwargs)

    def stop(self):
        self.sprite.add_force(Vector2.Cartesian(-sign(self.sprite.velocity.x) *
                                                min(abs(self.sprite.velocity.x),
                                                    maybe(self.sprite.on_platform).max_stopping_friction.
                                                    or_else(float('inf')))), 'stop movement')

        if self.direction not in Direction.idles:
            if self.direction == Direction.right:
                self.direction = Direction.idle_right
            if self.direction == Direction.left:
                self.direction = Direction.idle_left


class JumpControl(BaseControl):
    def __init__(self, jump_delay, sprite, direction, jump_force):
        BaseControl.__init__(self, sprite, direction)
        self.jump_force = jump_force
        self.jumping = False
        self.jump_timer = MySprites.Timer(jump_delay)

    def move(self, **kwargs):
        super(JumpControl, self).move(**kwargs)

    def jump(self):
        self.sprite.on_platform = None
        self.sprite.add_force(Vector2.Cartesian(0, -self.jump_force), 'jump')
        #  to stop the last movement

        self.jump_timer.activate()
        self.jumping = True

    def reset(self):
        self.jumping = False


class ManControl(LeftRightMovement, ShootControl, JumpControl):
    JUMP_FORCE = 750
    SHOT_DELAY = 0.4
    MOVING_SPEED = 350  # p/s

    def __init__(self, left_key, right_key, jump_key, shoot_key, man, init_direction, jump_delay):
        LeftRightMovement.__init__(self, ManControl.MOVING_SPEED, man, init_direction)
        ShootControl.__init__(self, init_direction, man, shot_delay=ManControl.SHOT_DELAY)
        JumpControl.__init__(self, jump_delay, man, init_direction, ManControl.JUMP_FORCE)
        self.shoot_key = shoot_key
        self.jump_key = jump_key
        self.right_key = right_key
        self.left_key = left_key

    def reset(self):
        BaseControl.reset(self)
        JumpControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        # print(self.in_control)
        pressed_keys = kwargs['keys']

        if self.sprite.is_dead:
            if self.direction == Direction.left:
                self.sprite.add_force(Vector2.Cartesian((self.sprite.moving_speed * self.sprite.mass)
                                                        , 0), 'friction')
                self.direction = Direction.idle_left

            if self.direction == Direction.right:
                self.sprite.add_force(Vector2.Cartesian((-self.sprite.moving_speed * self.sprite.mass)
                                                        , 0), 'friction')
                self.direction = Direction.idle_right
            return

        if pressed_keys[self.right_key] and (not pressed_keys[self.left_key]):  # moving right
            if self.direction == Direction.left:
                self.sprite.walk_left_animation.reset()
            elif self.direction == Direction.idle_left:
                self.sprite.idle_left_animation.reset()
            elif self.direction == Direction.idle_right:
                self.sprite.idle_right_animation.reset()
            self.direction = Direction.right

        elif pressed_keys[self.left_key] and (not pressed_keys[self.right_key]) :  # moving left
            if self.direction == Direction.right:
                self.sprite.walk_right_animation.reset()
            elif self.direction == Direction.idle_left:
                self.sprite.idle_left_animation.reset()
            elif self.direction == Direction.idle_right:
                self.sprite.idle_right_animation.reset()
            self.direction = Direction.left

        else:  # the user is pressing both right and left buttons or he is not pressing neither right or left
            self.stop()

        LeftRightMovement.move(self, **kwargs)

        if pressed_keys[self.jump_key] and self.jump_timer.finished() and self.sprite.on_platform:
            # jumping
            self.jump()

        if pressed_keys[self.shoot_key]:
            # shooting
            if self.direction in Direction.rights:
                self.shoot(Vector2.Cartesian(MySprites.GunBullet.SPEED))
                # self.shoot(Vector2.Cartesian(ManControl.MOVING_SPEED))
            else:
                self.shoot(Vector2.Cartesian(-MySprites.GunBullet.SPEED))
                # self.shoot(Vector2.Cartesian(-ManControl.MOVING_SPEED))


class TankControl(LeftRightMovement, TankShootControl):
    MOVING_SPEED = 350  # p/s
    SHOT_DELAY = 0.4
    TURRET_DELAY = 0.01

    def __init__(self, left_key, right_key, shoot_key, turret_up_key, turret_down_key, tank, init_direction):
        LeftRightMovement.__init__(self, TankControl.MOVING_SPEED, tank, init_direction)
        TankShootControl.__init__(self, init_direction, tank)
        self.turret_down_key = turret_down_key
        self.turret_up_key = turret_up_key
        self.shoot_key = shoot_key
        self.right_key = right_key
        self.left_key = left_key
        self.turret_move_timer = MySprites.Timer(TankControl.TURRET_DELAY)

    def reset(self):
        BaseControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        pressed_keys = kwargs['keys']
        next_direction = None
        if pressed_keys[self.right_key] and (not pressed_keys[self.left_key]):  # moving right
            self.sprite.moving_left_animation.reset()
            self.direction = Direction.right
        if pressed_keys[self.right_key] and (not pressed_keys[self.left_key]):  # moving right
            self.sprite.moving_left_animation.reset()
            self.direction = Direction.right

        elif pressed_keys[self.left_key] and (not pressed_keys[self.right_key]):  # moving left
            self.sprite.moving_right_animation.reset()
            self.direction = Direction.left

        else:  # the user is pressing both right and left buttons or he is not pressing neither right or left
            self.stop()

        LeftRightMovement.move(self, **kwargs)

        if pressed_keys[self.turret_up_key] and self.turret_move_timer.finished():
            self.sprite.change_turret_angle(1)
            self.turret_move_timer.activate()
        if pressed_keys[self.turret_down_key] and self.turret_move_timer.finished():
            self.sprite.change_turret_angle(-1)
            self.turret_move_timer.activate()

        if pressed_keys[self.shoot_key]:
            # shooting
            if self.direction in Direction.rights:
                self.shoot(Vector2.Polar(TankShootControl.SHOOT_SPEED, 360-self.sprite.turret_angle))
            else:
                self.shoot(Vector2.Polar(TankShootControl.SHOOT_SPEED, 180 + self.sprite.turret_angle))


class SimpleZombieControl(LeftRightMovement):
    MOVING_SPEED = 150  # p/s

    def __init__(self, zombie, starting_direction):
        LeftRightMovement.__init__(self, SimpleZombieControl.MOVING_SPEED, zombie, starting_direction)

    def move(self, **kwargs):
        if not self.in_control:
            return
        if self.sprite.is_dead:
            self.stop()
            # print(self.sprite.force, self.sprite.velocity, '\t', self.sprite.__class__.__name__)
        LeftRightMovement.move(self, **kwargs)
        """simply move the zombie as the direction above"""

    def platform_collide(self, direction, platform):
        if direction == Direction.horizontal:
            if self.direction == Direction.left:
                self.direction = Direction.right
            elif self.direction == Direction.right:
                self.direction = Direction.left


class NoMoveControl(BaseControl):
    pass
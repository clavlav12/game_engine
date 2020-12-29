from Engine.structures import Vector2, Direction
from Engine.Sound import Sounds
import Engine.pygame_structures as pg_structs
import pygame as pg
from numpy import sign
from pymaybe import maybe
from collections import namedtuple

controls = namedtuple('keys', ('up', 'down', 'left', 'right', 'cw', 'ccw'), defaults=(None, ) * 6)


def init(sound_player, MagazineClass, GunBulletClass):
    global player
    player = sound_player
    ShootControl.init(MagazineClass, GunBulletClass)


player = None


class BaseControl:
    def __init__(self, _sprite, _direction):
        self.sprite = _sprite
        self.direction = _direction
        self.in_control = True

    def move(self, **kwargs):  # {'sprites' : sprite_list, 'dtime': delta time, 'keys': keys}
        pass

    def sprite_collide(self, sprite, collision):
        pass

    def platform_collide(self, direction, platform, before):
        pass

    def reset(self):
        if self.direction in Direction.lefts:
            self.direction = Direction.idle_left
        elif self.direction in Direction.rights:
            self.direction = Direction.idle_right


class ShootControl(BaseControl):
    MAG_CAPACITY = 4
    MagazineClass = None  #
    GunBulletClass = None  #

    @classmethod
    def init(cls, MagazineClass, GunBulletClass):
        cls.MagazineClass = MagazineClass
        cls.GunBulletClass = GunBulletClass

    def __init__(self, direction, sprite, mag_capacity=MAG_CAPACITY, color="yellow", size='large', shot_delay=0.0):
        self.magazine = self.MagazineClass.Magazine(color, size, shot_delay, mag_capacity)
        BaseControl.__init__(self, sprite, direction)

    def shoot(self, velocity_vector):
        final_vector = Vector2.Copy(velocity_vector)
        final_vector.x += self.sprite.velocity.x

        if self.direction in Direction.rights:
            b = self.magazine.add_bullet(self.sprite.rect.right + 5, self.sprite.rect.center[1], final_vector)
        else:
            size = self.GunBulletClass.GunBullet.get_image_size(self.magazine.color, self.magazine.size)
            b = self.magazine.add_bullet(self.sprite.rect.left - size[0] - 5, self.sprite.rect.center[1], final_vector)
        if b is not None:
            player.play_sound(Sounds.gun_shot)


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
        # if self.sprite.on_platform:
        #     self.sprite.on_platform.stop_sprite(self.sprite)
        # else:
        self.sprite.add_force(Vector2.Cartesian(-sign(self.sprite.velocity.x) *
                                                min(abs(self.sprite.velocity.x),
                                                    maybe(self.sprite.on_platform).max_stopping_friction.
                                                    or_else(float('inf')))) * self.sprite.mass, 'stop movement')
        if self.direction not in Direction.idles:
            if self.direction == Direction.right:
                self.direction = Direction.idle_right
            if self.direction == Direction.left:
                self.direction = Direction.idle_left


class UpDownMovement:
    def __init__(self, moving_speed, sprite):
        self.moving_speed = moving_speed
        self.sprite = sprite

    def can_move(self):
        return True
        # return (not hasattr(self.sprite, 'on_platform') or bool(self.sprite.on_platform)) or (
        #         isinstance(self, JumpControl) and self.jumping)

    def move_up(self):
        self.sprite.add_force(Vector2.Cartesian(y=(-self.moving_speed - self.sprite.velocity.y) * self.sprite.mass),
                              'walking')

    def move_down(self):
        self.sprite.add_force(Vector2.Cartesian(y=(self.moving_speed - self.sprite.velocity.y) * self.sprite.mass),
                              'walking')

    def stop(self):
        self.sprite.add_force(Vector2.Cartesian(y=-sign(self.sprite.velocity.y) *
                                                min(abs(self.sprite.velocity.y),
                                                    maybe(self.sprite.on_platform).max_stopping_friction.
                                                    or_else(float('inf')))) * self.sprite.mass, 'stop movement')


class JumpControl(BaseControl):
    def __init__(self, jump_delay, sprite, direction, jump_force):
        BaseControl.__init__(self, sprite, direction)
        self.jump_force = jump_force
        self.jumping = False
        self.jump_timer = pg_structs.Timer(jump_delay)

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


class NoMoveControl(BaseControl):
    def __init__(self):
        super(NoMoveControl, self).__init__(None, None)

    def reset(self):
        pass


class AllDirectionMovement(LeftRightMovement):
    MOVING_SPEED = 350  # p/s

    def __init__(self, sprite, key_up=pg.K_UP,
                 key_down=pg.K_DOWN,
                 key_right=pg.K_RIGHT,
                 key_left=pg.K_LEFT):
        LeftRightMovement.__init__(self, AllDirectionMovement.MOVING_SPEED, sprite, Direction.idle_left)
        self.up_down_movement = UpDownMovement(self.MOVING_SPEED, sprite)
        self.key_left = key_left
        self.key_right = key_right
        self.key_down = key_down
        self.key_up = key_up

    def reset(self):
        BaseControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        pressed_keys = kwargs['keys']
        if pressed_keys[self.key_right]:  # moving right
            self.direction = Direction.right

        elif pressed_keys[self.key_left]:  # moving left
            self.direction = Direction.left

        else:  # the user is pressing both right and left buttons or he is not pressing neither right or left
            self.stop()

        LeftRightMovement.move(self, **kwargs)

        if pressed_keys[self.key_up]:
            self.up_down_movement.move_up()
        elif pressed_keys[self.key_down]:
            self.up_down_movement.move_down()
        else:
            self.up_down_movement.stop()


class Key:
    def __init__(self, key, is_pressed=False):
        self.key = key
        self.pressed = is_pressed

    def press(self):
        self.pressed = True

    def release(self):
        self.pressed = False

    def first_pressed(self):
        was_pressed = self.pressed
        self.press()
        return not was_pressed

    def set_pressed(self, value):
        self.pressed = value

    def set_pressed_auto(self, keys):
        was_pressed = self.pressed
        self.pressed = keys[self.key]
        return (not was_pressed) and self.pressed

    def __str__(self):
        return str(self.key)


class AllDirectionSpeed(LeftRightMovement):
    MOVING_SPEED = 350  # p/s

    def __init__(self, sprite,
                 key_up=pg.K_UP,
                 key_down=pg.K_DOWN,
                 key_right=pg.K_RIGHT,
                 key_left=pg.K_LEFT):
        LeftRightMovement.__init__(self, self.MOVING_SPEED, sprite, Direction.idle_left)
        self.up_down_movement = UpDownMovement(self.MOVING_SPEED, sprite)
        self.set_controls(key_up, key_down, key_left, key_right)

    def set_controls(self, key_up, key_down, key_left, key_right):
        self.controls = controls(*(Key(x) for x in (key_up, key_down, key_left, key_right)))

    def reset(self):
        BaseControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        pressed_keys = kwargs['keys']

        direction = Direction.idle_right
        new_press = self.controls.right.set_pressed_auto(pressed_keys)
        if new_press:  # moving right
            direction = Direction.right
        new_press = self.controls.left.set_pressed_auto(pressed_keys)
        if new_press:  # moving right
            direction = Direction.left

        self.direction = direction
        LeftRightMovement.move(self, **kwargs)

        new_press = self.controls.up.set_pressed_auto(pressed_keys)
        if new_press:  # moving up
            self.up_down_movement.move_up()
        new_press = self.controls.down.set_pressed_auto(pressed_keys)
        if new_press:  # moving up
            self.up_down_movement.move_down()


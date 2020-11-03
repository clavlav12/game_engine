from Engine.structures import Vector2, Direction
from Engine.Sound import Sounds
import Engine.pygame_structures as pg_structs
from numpy import sign
from pymaybe import maybe


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
    pass

import Engine.base_control as base_controls
import Engine.base_sprites as base_sprites
import Engine.pygame_structures as pygame_structures
import Engine.structures as structures
import Engine.Sound as Sound
import Engine.Particle as Particle
import pygame
import math


class MissileMagazine(pygame.sprite.Group):
    magazines_list = []

    def __init__(self, shot_delay, capacity, tank, damage=base_sprites.GunBullet.DAMAGE):
        super(MissileMagazine, self).__init__()
        self.capacity = capacity
        self.shot_timer = pygame_structures.Timer(shot_delay)
        self.damage = damage
        self.tank = tank
        base_sprites.Magazine.magazines_list.append(self)

    def add_bullet(self, velocity_vector):
        if self.shot_timer.finished() and not self.full():
            self.shot_timer.activate()
            bull = Missile(self.tank.control.direction, self.tank, velocity_vector)
            self.add(bull)
            return bull
        return None

    def full(self):
        return len(self) >= self.capacity


class TankShootControl(base_controls.BaseControl):
    MAG_CAPACITY = 1
    SHOT_DELAY = 1
    # SHOOT_SPEED = 1000
    SHOOT_SPEED = 1500

    def __init__(self, direction, sprite, mag_capacity=MAG_CAPACITY, shot_delay=SHOT_DELAY):
        self.magazine = MissileMagazine(shot_delay, mag_capacity, sprite)
        base_controls.BaseControl.__init__(self, sprite, direction)

    def shoot(self, velocity_vector):
        # final_vector = Vector2.Copy(velocity_vector)
        # final_vector.x += self.sprite.velocity.x
        b = self.magazine.add_bullet(velocity_vector)
        if b is not None:
            """play sound!"""
            pass
            # MySprites.player.play_sound(Sounds.gun_shot)


class TankControl(base_controls.LeftRightMovement, TankShootControl):
    MOVING_SPEED = 350  # p/s
    SHOT_DELAY = 0.4
    TURRET_DELAY = 0.01

    def __init__(self, left_key, right_key, shoot_key, turret_up_key, turret_down_key, tank, init_direction):
        base_controls.LeftRightMovement.__init__(self, TankControl.MOVING_SPEED, tank, init_direction)
        TankShootControl.__init__(self, init_direction, tank)
        self.turret_down_key = turret_down_key
        self.turret_up_key = turret_up_key
        self.shoot_key = shoot_key
        self.right_key = right_key
        self.left_key = left_key
        self.turret_move_timer = pygame_structures.Timer(TankControl.TURRET_DELAY)

    def reset(self):
        base_controls.BaseControl.reset(self)

    def move(self, **kwargs):
        if not self.in_control:
            return
        pressed_keys = kwargs['keys']
        next_direction = None
        if pressed_keys[self.right_key] and (not pressed_keys[self.left_key]):  # moving right
            self.sprite.moving_left_animation.reset()
            self.direction = structures.Direction.right
        if pressed_keys[self.right_key] and (not pressed_keys[self.left_key]):  # moving right
            self.sprite.moving_left_animation.reset()
            self.direction = structures.Direction.right

        elif pressed_keys[self.left_key] and (not pressed_keys[self.right_key]):  # moving left
            self.sprite.moving_right_animation.reset()
            self.direction = structures.Direction.left

        else:  # the user is pressing both right and left buttons or he is not pressing neither right or left
            self.stop()

        base_controls.LeftRightMovement.move(self, **kwargs)

        if pressed_keys[self.turret_up_key] and self.turret_move_timer.finished():
            self.sprite.change_turret_angle(1)
            self.turret_move_timer.activate()
        if pressed_keys[self.turret_down_key] and self.turret_move_timer.finished():
            self.sprite.change_turret_angle(-1)
            self.turret_move_timer.activate()

        if pressed_keys[self.shoot_key]:
            # shooting
            if self.direction in structures.Direction.rights:
                self.shoot(structures.Vector2.Polar(TankShootControl.SHOOT_SPEED, 360-self.sprite.turret_angle))
            else:
                self.shoot(structures.Vector2.Polar(TankShootControl.SHOOT_SPEED, 180 + self.sprite.turret_angle))


def sign(a):
    if a > 0:
        return 1
    elif a < 0:
        return -1
    return 0


class Tank(base_sprites.Vehicle):
    scale = 0.5
    position_offset = (85 * scale, 98 * scale)
    pivot_offset = (-20 * scale, 0)
    TURRET_IMAGE = pygame.transform.flip(pygame.image.load('images/main-turret.png'), True, False).convert_alpha()
    TURRET_IMAGE = pygame_structures.smooth_scale_image(TURRET_IMAGE, scale)

    MOVE_LEFT_IMAGES = pygame_structures.get_images_list(r'animation\tank' + '\\[1-9]*.png', scale)
    pygame_structures.smooth_scale_images(MOVE_LEFT_IMAGES, scale)
    MOVE_RIGHT_IMAGES = [pygame.transform.flip(x, True, False).convert_alpha() for x in MOVE_LEFT_IMAGES]
    HIT_POINTS = 2000

    def __init__(self, init_direction, position, left_key=pygame.K_LEFT, right_key=pygame.K_RIGHT,
                 shoot_key=pygame.K_SPACE,
                 turret_up_key=pygame.K_UP, turret_down_key=pygame.K_DOWN, health_bar_color=None):
        self.moving_left_animation = pygame_structures.Animation.by_images_list(Tank.MOVE_LEFT_IMAGES, 10)
        self.moving_right_animation = pygame_structures.Animation.by_images_list(Tank.MOVE_RIGHT_IMAGES, 10)
        if init_direction == structures.Direction.right:
            self.image = self.moving_right_animation.get_image()
        elif init_direction == structures.Direction.left:
            self.image = self.moving_left_animation.get_image()
        super(Tank, self).__init__(self.image.get_rect(),
                                   TankControl(left_key, right_key, shoot_key, turret_up_key, turret_down_key
                                                        , self, init_direction),
                                   1, (0, 0), Tank.HIT_POINTS, health_bar_color)
        self.rect.topleft = position
        self.position.values = self.rect.topleft
        self.turret_angle = 0
        self.turret_image = pygame_structures.FlippableRotatedImage(Tank.TURRET_IMAGE, self.turret_angle, Tank.pivot_offset,
                                                  Tank.position_offset,
                                                  self.rect, structures.Direction.left)

    def set_turret_angle(self, angle):
        self.turret_angle = max(min((abs(angle) % 380) * sign(angle), 116), -45)
        self.turret_image.rotate(self.turret_angle)

    def change_turret_angle(self, angle_change):
        self.set_turret_angle(self.turret_angle + angle_change)

    def draw(self):
        if self.hit_points > 0:
            self.turret_image.blit_image(self.control.direction)
            if self.control.direction == structures.Direction.right:
                self.image = self.moving_right_animation.get_image()
            elif self.control.direction == structures.Direction.left:
                self.image = self.moving_left_animation.get_image()
            super(Tank, self).draw()

        # self.draw_rect()


class Missile(base_sprites.Bullet):
    DAMAGE = 1
    TRAVEL_DISTANCE = 1500
    MISSILE_IMAGE = pygame.image.load(r'images\missile.png').convert_alpha()
    MISSILE_IMAGE = pygame_structures.smooth_scale_image(MISSILE_IMAGE, 1.5)

    def __init__(self, init_direction, tank: Tank, shoot_force):
        turret_angle = tank.turret_angle
        turret_obj = tank.turret_image
        r = Missile.MISSILE_IMAGE.get_rect()

        if init_direction in structures.Direction.rights:
            turret_rect = turret_obj.right_image.rect
            if turret_angle > 0:
                r.bottomleft = turret_rect.topright
            elif turret_angle <= 0:
                r.topleft = turret_rect.bottomright

        elif init_direction in structures.Direction.lefts:
            turret_rect = turret_obj.left_image.rect
            if turret_angle > 0:
                r.bottomright = turret_rect.topleft
            elif turret_angle <= 0:
                r.topright = turret_rect.bottomleft
        super(Missile, self).__init__(r, Missile.DAMAGE, Missile.TRAVEL_DISTANCE)
        self.missile_image = pygame_structures.RotatableImage(Missile.MISSILE_IMAGE, 0, (0, 0), lambda: self.rect.topleft)
        self.total_movement = 0
        self.killed = False
        self.shoot_force = shoot_force
        self.rect_collision = False

    def draw(self):
        self.missile_image.rotate(int(self.velocity.theta))
        self.image = self.missile_image.blit_image()
        self.rect.width = self.missile_image.rect.width
        self.rect.height = self.missile_image.rect.height
        self.rect.topleft = self.missile_image.rect.topleft
        # self.draw_rect()

    def _update(self, control_dict):
        if self.first_frame:
            self.add_force(self.shoot_force, "shoot", True)
        self.total_movement = 0
        self.operate_gravity()
        super(Missile, self)._update(control_dict)
        self.travel_distance -= math.sqrt(self.total_movement)
        self.first_frame = False

    def update_position(self, axis, time_delta):
        if self.travel_distance <= 0:
            self.kill()
        self.total_movement += abs(self.velocity.x * time_delta) ** 2
        super(Missile, self).update_position(axis, time_delta)

    def kill(self):
        if not self.killed:
            pygame_structures.Camera.shake()
            base_sprites.player.play_sound(Sound.Sounds.explosion)
            pygame_structures.Camera.add_particle(Particle.Explosion, self.rect.center, collide_function=self.explosion_collide)
            super(Missile, self).kill()
            self.killed = True

    def explosion_collide(self, other):
        if isinstance(other, base_sprites.AdvancedSprite) and not other.is_dead:
            if other.resistance_timer.finished():
                other.hit_points -= self.damage
                other.resistance_timer.activate()

    def collision(self, other):
        if self.first_frame:
            return
        if (isinstance(other, base_sprites.AdvancedSprite)) and not other.is_dead:
            if other.resistance_timer.finished():
                other.hit_points -= self.damage
                other.resistance_timer.activate()
            self.kill()
            return False
        elif isinstance(other, base_sprites.Bullet):
            self.kill()
            return False



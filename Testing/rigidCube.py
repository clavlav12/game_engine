from Engine import pygame_structures
from Engine import base_sprites
from Engine import base_control
from Engine import structures
import pygame as pg
import math
import random


class RigidCube(base_sprites.AdvancedSprite):
    GRAVITY = 10000

    def __init__(self, size, x, y):
        rect = pg.Rect(
            x - size//2,
            y - size//2,
            size, size
        )
        super(RigidCube, self).__init__(rect, base_control.NoMoveControl(), 10**4, 0)

        self.angle = int(30)
        self.angle = random.randrange(90)
        self.last_angle = self.angle
        self.angular_velocity = 0
        self.angular_acceleration = 0
        self.torque = 0
        self.moment_of_inertia = size ** 4 / 12
        self.moment_of_inertia = size ** 4 / 36
        self.size = size
        image = pg.Surface((size, size), pg.SRCALPHA, 32)
        image.fill(pg.Color('blue'))
        half_diagonal = self.size * math.sqrt(2) / 4
        # print(half_diagonal)
        self.real_image = pygame_structures.RotatableImage(image, self.angle, (0, 0), lambda: self.rect.center)

        # pygame_structures.Camera.set_scroller_position(self)

    def to_dict(self):
        before = {
            'rect': pg.Rect(*self.rect),
            'on_platform': self.on_platform,
            'position': self.position.copy(),
            'velocity': self.velocity.copy(),
            'force': self.force.copy(),
        }
        if hasattr(self.control, 'jumping'):
            before['jumping'] = self.jumping
        return before

    def operate_gravity(self):
        super(RigidCube, self).operate_gravity()
        if self.on_platform:
            self.torque = - structures.DegTrigo.sin(45 - self.angle) * self.size * (math.sqrt(2)/2) * self.mass * \
                          self.GRAVITY

    def on_platform_collision(self, direction, platform, before):
        super(RigidCube, self).on_platform_collision(direction, platform, before)
        # print(self.angular_velocity)
        if before['velocity'].magnitude() > 0:
            # return
            # print(self.angular_velocity, (before['velocity'].magnitude() / (math.sqrt(2) * self.size/2)))
            self.angular_velocity += (before['velocity'].magnitude() / 3)
            # self.angular_velocity += (before['velocity'].magnitude() / (math.sqrt(2) * self.size/2))

    def update_kinematics(self, time_delta):
        # if round(self.angle) % 90 in (1, -1, 0):
        if round(self.angle) % 90 in (1, -1, 0):
            self.torque = 0
            self.angular_velocity = 0
            self.angle = 0
        super(RigidCube, self).update_kinematics(time_delta)
        self.angular_acceleration = self.torque / self.moment_of_inertia
        self.angular_velocity += self.angular_acceleration * time_delta
        self.last_angle = self.angle
        self.angle += self.angular_velocity * time_delta
        self.torque = 0

    def draw(self):
        self.real_image.rotate(self.angle)
        self.image = self.real_image.blit_image()
        # self.rect.width = self.real_image.rect.width
        # self.rect.height = self.real_image.rect.height
        # self.rect.topleft = self.real_image.rect.topleft
        # self.draw_rect()
        # print(self.rect.bottom,  "bottom")

    def collision(self, other):
        print(self.velocity.magnitude())
        if round(self.velocity.magnitude()) > 0:
            self.angular_velocity += (self.velocity.magnitude() / 3)
            print(round(self.velocity.magnitude()))
        self.torque = - structures.DegTrigo.sin(45 - (other.angle - self.angle)) * self.size * (math.sqrt(2) / 2) * self.mass * \
                      self.GRAVITY
        self.sprite_collide_func(other, structures.Direction.vertical)
        return True

    def sprite_collide_func(self, _sprite, axis):
        # if not sprite.collide_mask(self, _sprite):
        #     return
        # print(self.rect.topleft)
        if axis == structures.Direction.vertical:
            # print("velocity: ", _sprite.velocity.y)
            if _sprite.velocity.y > 0:  # hit from top
                # while _sprite.collide_mask(_sprite, self):
                #     _sprite.position.y -= 1
                #     _sprite.rect.y -= 1
                _sprite.rect.bottom = self.rect.top
                was_on = _sprite.on_platform
                _sprite.on_platform = self
            else:  # hit from bottom
                _sprite.rect.top = self.rect.bottom
            _sprite.position.y = _sprite.rect.y
            _sprite.force.y = 0
            _sprite.velocity.y = 0
            if hasattr(_sprite.control, 'jumping') and _sprite.control.jumping:
                _sprite.control.jumping = False
                _sprite.on_platform = None

        else:
            if _sprite.velocity.x > 0:  # hit from left
                _sprite.rect.right = self.rect.left
            else:  # hit from right
                _sprite.rect.left = self.rect.right
            _sprite.position.x = _sprite.rect.x
            _sprite.force.x = 0
            _sprite.velocity.x = 0




def main():
    W = 1000
    H = 700
    screen = pygame_structures.DisplayMods.Windowed((W, H))
    pygame_structures.Camera.init(screen, "static", None)

    sur = pg.Surface((50, 50)).convert()
    sur.fill((0, 255, 255))
    tile_list = [
        [(3,) for _ in range(50)] for __ in range(50)
    ]
    size = 50
    for i in range(0, W//size + 20):
        tile_list[(H-size)//size][i] = (1, sur)

    pygame_structures.Map(tile_list, [], [], [], size)
    fps = 1000
    elapsed = 1 / fps
    running = True
    while running:
        events = pg.event.get()
        for event in events:
            if event.type == pg.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pg.QUIT:
                running = 0
            elif event.type == pg.KEYDOWN:
                pass
            elif event.type == pg.MOUSEBUTTONDOWN:
                RigidCube(50, *event.pos)

        keys = pg.key.get_pressed()
        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    main()

import os
import pygame
import pygame as pg
import math
from Engine.structures import VectorType, Vector2, Direction, DegTrigo
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures
import random

W = 1000
H = 700
# screen = DisplayMods.Windowed((1680, 1080))
screen = pygame_structures.DisplayMods.Windowed((W, H))
W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

pygame_structures.Camera.init(screen, "dynamic", None)


# pygame_structures.Camera.init(screen, "static", None)


# class Planet(base_sprites.BaseSprite):
#
#
#
#     def __init__(self, x, y):
#         self.image.convert_alpha()
#         super(Planet, self).__init__(pygame.Rect(x, y, 50, 50),
#                                      base_control.BaseControl(self, Direction.right), 1)

class RigidCube(base_sprites.AdvancedSprite):
    GRAVITY = 10000

    def __init__(self, size, x, y):
        rect = pg.Rect(
            x - size//2,
            y - size//2,
            size, size
        )
        super(RigidCube, self).__init__(rect, base_control.NoMoveControl(), 10**4, 0)

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

    def collision(self, other, collision):
        # print(self.velocity.magnitude())
        if round(self.velocity.magnitude()) > 0:
            self.angular_velocity += (self.velocity.magnitude() / 3)
            # print(round(self.velocity.magnitude()))
        return True


def Main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame_structures.Map.No_Map()
    running = 1
    fps = 1000
    elapsed = 1 / fps
    for _ in range(100):
        RigidCube(50, _ * 101, _ * 101)
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0

        keys = pg.key.get_pressed()
        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    Main()

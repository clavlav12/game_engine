import os
import pygame
import math
from Engine.structures import VectorType, Vector2, Direction, DegTrigo
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures
import random

W = 1000
H = 700


# screen = pygame_structures.DisplayMods.NoWindow()
screen = pygame_structures.DisplayMods.Windowed((W, H))

W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

pygame_structures.Camera.init(screen, "dynamic", None)


class Ball(base_sprites.BaseSprite):

    r = 25
    image = pygame_structures.AutoConvertSurface(pygame.Surface((r*2, r*2), pygame.SRCALPHA))

    def __init__(self):

        pygame.draw.circle(self.image, pygame.Color('white'), (self.r, self.r), self.r)

        super(Ball, self).__init__(
            self.image.get_rect(),
            base_control.NoMoveControl(),
            50
        )

        self.velocity.set_values(500, -500)
        self.set_position(0, H/2)

    def update(self, kwargs):
        self.apply_gravity()


def Main():
    pygame_structures.Map([], [], [], [], 50)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    import pyexcel
    lst = []
    b = Ball()

    timer = pygame_structures.Timer(5, True)
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] and keys[pygame.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()

        lst.append(
            {
                "x": b.position.x,
                "y": b.position.y
            },
        )
        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)
        if timer.finished():
            running = 0

    pyexcel.save_as(records=lst, dest_file_name="your_file.xls")


if __name__ == '__main__':
    Main()

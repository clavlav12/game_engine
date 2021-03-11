import pygame
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures


class Ball(base_sprites.BaseSprite):

    # r = 25
    # image = pygame_structures.AutoConvertSurface(pygame.Surface((r*2, r*2), pygame.SRCALPHA))

    def __init__(self, r):
        r = int(r)
        self.image = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, pygame.Color('white'), (r, r), r)

        super(Ball, self).__init__(
            self.image.get_rect(),
            base_control.AllDirectionMovement(self),
            50
        )

        # self.velocity.set_values(500, -500)
        self.set_position(350, 0)
        print("initiated with velocity: ", self.velocity)

    def update(self, kwargs):
        self.apply_gravity()

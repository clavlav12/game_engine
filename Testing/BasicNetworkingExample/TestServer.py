import os
import pygame
import math
from Engine.structures import VectorType, Vector2, Direction, DegTrigo
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures
import random
from Engine.Networking.Server import GameServer, CommandServer
from common_sprites import *
import threading
W = 1000
H = 700

print(base_sprites.BaseSprite.classes)

class Server(GameServer):
    @CommandServer.command('Connect')
    def connect(self, user, kwargs):
        super(Server, self).connect(user, kwargs)
        self.sprite = self.create_sprite(Ball, user, r=25)


def Main():
    screen = pygame_structures.DisplayMods.NoWindow()
    # screen = pygame_structures.DisplayMods.Windowed((W, H))

    pygame_structures.Camera.init(screen, "dynamic", None)

    pygame_structures.Map([], [], [], [], 50)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    # print("before")
    threading.Thread(target=Server).start()
    # print("after")
    # sprite = Server.instance.create_sprite(Ball, r=25)

    timer = pygame_structures.Timer(float('inf'), True)
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0

            if event.type == pygame.KEYDOWN:
                client.key_event(event.key, 1)

            if event.type == pygame.KEYUP:
                client.key_event(event.key, 0)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] and keys[pygame.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()

        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)
        if timer.finished():
            running = 0


if __name__ == '__main__':
    Main()

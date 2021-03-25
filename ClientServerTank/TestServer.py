import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import pygame
import math
from Engine.structures import VectorType, Vector2, Direction, DegTrigo
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures
from server import Server
from common_sprites import *
import threading
import random


def Main():
    screen = pygame_structures.DisplayMods.NoWindow()
    # screen = pygame_structures.DisplayMods.Windowed((W, H))
    pygame.display.set_caption('Server')
    pygame_structures.Camera.init(screen, "dynamic", None)

    load_map()
    running = 1
    fps = 1000
    elapsed = 1 / fps

    # print("before")
    server = threading.Thread(target=Server)
    server.start()
    # print("after")
    # sprite = Server.instance.create_sprite(Ball, r=25)

    timer = pygame_structures.Timer(float('inf'), True)
    fps_sum = 0
    num_of_frames = 0

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0

            # if event.type == pygame.KEYDOWN:
            #     client.key_event(event.key, 1)
            #
            # if event.type == pygame.KEYUP:
            #     client.key_event(event.key, 0)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] and keys[pygame.K_r]:
            base_sprites.BaseSprite.sprites_list.empty()

        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 5 / fps)
        if timer.finished():
            running = 0

        fps_sum += base_sprites.clock.get_fps()
        num_of_frames += 1

    # server.raise_exception()
    print(f'{fps_sum / num_of_frames:.02f}')
    Server.instance.server_socket.close()


if __name__ == '__main__':
    Main()

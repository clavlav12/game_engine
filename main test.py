import os
import pygame
from pygame import *
from GlobalUse import DisplayMods
import math
from structures import VectorType, Vector2
import inspect
import decimal
import sys

W = 1000
H = 700
screen = DisplayMods.Windowed((W, H))
from MySprites import *
import time
# Camera.init(screen, "dynamic", None)
Camera.init(screen, "static", None)


def get_color(hitpoints):
    if hitpoints > 1000:
        return Color('green')
    elif hitpoints > 500:
        return Color('dark green')
    elif hitpoints > 100:
        return Color('orange')
    elif hitpoints > 50:
        return Color('dark orange')
    else:
        return Color('red')


def get_color(hitpoints):
    return int(255-hitpoints*255/2000), int(hitpoints*255/2000), 0


def Main():
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    # man = Man(600, 200, K_SPACE, K_RIGHT, K_LEFT, K_RETURN, ((0, 255, 0), (255, 0, 0)), 'M')
    # man.rect.bottom = 400
    # man.position.values = man.rect.topleft
    tank1 = Tank(Direction.right, (600, 200), shoot_key=K_KP_ENTER, health_bar_color=(Color('red'), Color('green')))
    tank2 = Tank(Direction.right, (200, 200), K_a, K_d, K_SPACE, K_w, K_s, health_bar_color=(Color('red'), Color('green')))
    # man = Man(200, 200, K_t, K_h, K_f, K_g, (Color('blue'), Color('light blue')), 'avi')
    # man = Man(400, 20, K_UP, K_RIGHT, K_LEFT, K_SPACE, (Color('blue'), Color('light blue')), 'avi2')
    Camera.set_scroller_position(tank2, smooth_move=True)
    sur = Surface((50, 50)).convert()
    sur.fill((0, 0, 255))
    sur2 = Surface((50, 50))
    sur2.fill((255, 0, 0))
    tile_list = [
        [(3,) for _ in range(50)] for __ in range(50)
    ]
    size = 50
    for i in range(0, W//size + 20):
        tile_list[(H-size)//size][i] = (1, sur)
    for i in range(H//50-1, H//50-7, -1):
        tile_list[i][(W//2 - 25)//size] = (1, sur)

    # Map(tile_list, [], [], [], size)
    Map(tile_list, tile_list, tile_list, tile_list, size)
    # print(*[['1' if not isinstance(tile, air) else '0' for tile in column] for column in Map.get_map(1, 1)], sep='\n')
    # print(*[['1' if not isinstance(tile, air) else '0' for tile in column] for column in Map.get_map(1, 1)], sep='\n')
    # man.rect.left = b.rect.left
    # man.rect.bottom = b.rect.top
    # man.position.values = man.rect.topleft
    # BlockingBlock(sur, -2500, 300)
    # zombie = Zombie(100, 300)
    # zombie.rect.bottom = 0
    # zombie.position.y = zombie.rect.y
    running = 1
    timer = Timer(0.25)
    show = Timer(0.05)
    show.activate()
    fps = 1000
    elapsed = 1/fps
    fnt = font.SysFont('comicsansms', 12)
    is_zombie = False
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == WINDOWEVENT:
                clock.tick()
                continue
            if event.type == pygame.QUIT:
                running = 0
            elif event.type == pygame.KEYDOWN:
                pass
        # print(tank1.rect.center)
        first = fnt.render(f'Hit Points: {tank1.hit_points}', True, get_color(tank1.hit_points))
        second = fnt.render(f'Hit Points: {tank2.hit_points}', True, get_color(tank2.hit_points))
        # if keys[K_KP_ENTER] and timer.finished():
        #     a = Timer(2, True)
        #     print(a.finished())
        #
        #     if is_zombie:
        #         Camera.set_scroller_position(man, True)
        #     else:
        #         Camera.set_scroller_position(zombie, True)
        #     is_zombie = not is_zombie
        #     timer.activate()
        keys = pygame.key.get_pressed()
        tick(elapsed, clock, keys)
        Camera.blit(first, (W - 150, 50))
        Camera.blit(second, (5, 50))
        Camera.post_process()
        pygame.display.flip()
        elapsed = min(clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    Main()

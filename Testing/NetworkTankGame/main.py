from Engine.Debug import *
from Engine import base_sprites
from Engine import base_control
from Engine.structures import Vector2

import pygame as pg
import os


def Main():
    W = 1000
    H = 700

    screen = pygame_structures.DisplayMods.Windowed((W, H))
    W, H = pygame_structures.DisplayMods.current_width, pygame_structures.DisplayMods.current_height

    pygame_structures.Camera.init(screen, "dynamic", None)

    import sprites

    os.environ['SDL_VIDEO_CENTERED'] = '1'

    ts = 25

    tile_list = [
        [{'id': 3} for _ in range(W//ts)] for __ in range(H//ts)
    ]

    sur = pg.Surface((ts, ts)).convert()
    sur.fill((0, 0, 255))

    collection = pygame_structures.TileCollection()
    for i in range(0, W//ts):
        tile_list[0][i] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, W//ts):
        tile_list[H//ts-1][i] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, H//ts):
        tile_list[i][W//ts-1] = {'id': 1, 'img': sur, 'group': collection}

    collection = pygame_structures.TileCollection()
    for i in range(0, H//ts):
        tile_list[i][0] = {'id': 1, 'img': sur, 'group': collection}

    # tile_list[0][0] = {'id': 6, 'group': collection}
    pygame_structures.Map(
        tile_list, [], [], [], ts)
    running = 1
    fps = 1000
    elapsed = 1 / fps

    hbc = (pg.Color('green'), pg.Color('red'))
    sprites.Tank(Vector2.Cartesian(1, 0).normalized(), (W - 100, H / 2),
                 base_control.wasd, pg.K_SPACE, sprites.Color.green, hbc)
    sprites.Tank(Vector2.Cartesian(-1, 0).normalized(),
                 (100, H/2), base_control.arrows, pg.K_KP_ENTER, sprites.Color.black, hbc)

    while running:
        events = pg.event.get()
        for event in events:

            if event.type == pg.WINDOWEVENT:
                base_sprites.clock.tick()
                continue
            if event.type == pg.QUIT:
                running = 0

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_y:
                    d1.make_gold()

        keys = pg.key.get_pressed()
        base_sprites.tick(elapsed, keys)
        pygame_structures.Camera.post_process(base_sprites.BaseSprite.sprites_list)
        pg.display.flip()
        elapsed = min(base_sprites.clock.tick(fps) / 1000.0, 1 / 15)
        # elapsed = 1/800




if __name__ == '__main__':
    Main()

import os
import pygame
from Engine.pygame_structures import DisplayMods, Camera, Map, Timer, TileCollection
from Engine.structures import VectorType, Vector2, Direction
from Engine.base_sprites import clock, tick, BaseSprite
import Engine.base_sprites as base_sprites
from sprites import Tank

base_sprites.GRAVITY = 3000

def get_color(hitpoints):
    if hitpoints > 1000:
        return pygame.Color('green')
    elif hitpoints > 500:
        return pygame.Color('dark green')
    elif hitpoints > 100:
        return pygame.Color('orange')
    elif hitpoints > 50:
        return pygame.Color('dark orange')
    else:
        return pygame.Color('red')


def get_color(hitpoints):
    return int(255-hitpoints*255/2000), int(hitpoints*255/2000), 0


def Main():
    W = 1000
    H = 700
    screen = DisplayMods.Windowed((W, H))
    # screen = DisplayMods.NoWindow()
    W = 1000
    H = 700


    Camera.init(screen, "static", None)
    # Camera.init(screen, "static", None)
    # man = Man(600, 200, K_SPACE, K_RIGHT, K_LEFT, K_RETURN, ((0, 255, 0), (255, 0, 0)), 'M')
    # man.rect.bottom = 400

    # man.position.values = man.rect.topleft
    tank1 = Tank(Direction.right, (600, 200), shoot_key=pygame.K_KP_ENTER, health_bar_color=(pygame.Color('green'), pygame.Color('red')))

    tank2 = Tank(Direction.right, (200, 200), pygame.K_a, pygame.K_d, pygame.K_SPACE, pygame.K_w, pygame.K_s, health_bar_color=(pygame.Color('green'), pygame.Color('red')))
    # man = Man(200, 200, K_t, K_h, K_f, K_g, (Color('blue'), Color('light blue')), 'avi')
    # man = Man(400, 20, K_UP, K_RIGHT, K_LEFT, K_SPACE, (Color('blue'), Color('light blue')), 'avi2')

    sur = pygame.Surface((50, 50))
    sur.fill((0, 0, 255))
    sur2 = pygame.Surface((50, 50))
    sur2.fill((255, 0, 0))
    tile_list = [
        [{'id': 3} for _ in range(50)] for __ in range(50)
    ]
    size = 50
    collection = TileCollection()
    for i in range(0, W//size):
        tile_list[(H-size)//size][i] = {'id': 1, 'img': sur, 'group': collection}
    # for i in range(0, W//size + 20):
    #     tile_list[(H-size)//size - 1][i] = (4, size)

    collection = TileCollection()
    for i in range(H//50-1, H//50-7, -1):
        tile_list[i][(W//2 - 25)//size] = {'id': 1, 'img': sur, 'group': collection}

    Map(tile_list, [], [], [], size)
    # Map(tile_list, tile_list, tile_list, tile_list, size)
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
    fnt = pygame.font.SysFont('comicsansms', 12)
    is_zombie = False
    # Camera.set_scroller_position(tank2, smooth_move=True)

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.WINDOWEVENT:
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
        tick(elapsed, keys)


        Camera.blit(first, (W - 150, 50))
        Camera.blit(second, (5, 50))

        # print(tank1.position)
        Camera.post_process(BaseSprite.sprites_list)
        elapsed = min(clock.tick(fps) / 1000.0, 5 / fps)


if __name__ == '__main__':
    Main()

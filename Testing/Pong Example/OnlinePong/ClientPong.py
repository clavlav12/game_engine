from Engine.Networking.Client import GameClient
import Engine.base_sprites as base_sprites
import Engine.pygame_structures as pygame_structures
import pygame
import common_sprites as csp

GameClient().start()

cheat = False
if cheat:
    screen = pygame_structures.DisplayMods.Windowed((csp.W * 2, csp.H * 2))
    pygame.display.set_caption('FoV hack Client')
else:
    screen = pygame_structures.DisplayMods.Windowed((csp.W, csp.H))
    pygame.display.set_caption('Client')

pygame_structures.Camera.init(screen, "dynamic", None)
csp.make_map()
base_sprites.basic_loop()



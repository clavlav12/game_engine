from Engine.Networking.Server import GameServer, User
import Engine.base_sprites as base_sprites
import Engine.base_control as base_control
import Engine.pygame_structures as pygame_structures
import pygame
import threading
import common_sprites as csp
import random
from time import sleep


class PongServer(GameServer):
    def connect(self, user, _):
        print("here")
        super(PongServer, self).connect(user, {})
        if len(User.users_list) == 2:
            self.start_game()

    def start_game(self):
        print("Starting")
        user1, user2 = User.users_list.values()
        OFFSET = 50

        self.create_sprite(csp.Bat, controller=user1, position=(OFFSET, csp.H // 2))
        # sleep(1)
        self.create_sprite(csp.Bat, controller=user2, position=(csp.W - OFFSET, csp.H // 2))
        # sleep(1)
        self.create_sprite(csp.Ball, position=(csp.W // 2, csp.H // 2 - 150), angle=random.randint(-30, 30))


server = threading.Thread(target=PongServer)
server.start()

screen = pygame_structures.DisplayMods.NoWindow()
pygame.display.set_caption('Server')
pygame_structures.Camera.init(screen, "dynamic", None)
csp.make_map()
base_sprites.basic_loop()



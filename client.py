# from socket import socket
# import pygame
# import pickle
#
# W = 1000
# H = 700
# win = pygame.display.set_mode((W, H))
# my_socket = socket()
# my_socket.connect(('127.0.0.1', 5151))
# HEADERSIZE = 10
#
#
# class Test:
#     def __init__(self, surface):
#         self.surface = surface
#         self.name = "Test"
#
#     def __getstate__(self):
#         state = self.__dict__.copy()
#         surface = state.pop("surface")
#         state["surface_string"] = (pygame.image.tostring(surface, "RGB"), surface.get_size())
#         return state
#
#     def __setstate__(self, state):
#         surface_string, size = state.pop("surface_string")
#         state["surface"] = pygame.image.fromstring(surface_string, size, "RGB")
#         self.__dict__.update(state)
#
# # data_string = pickle.dumps(variable)
# # s.send(data_string)
#
# # data = conn.recv(4096)
# # data_variable = pickle.loads(data)
#
#
# while True:
#     data_length = my_socket.recv(10)
#     print(int(data_length))
#     if not data_length:
#         break
#     data = my_socket.recv(int(data_length))
#     data_variable = pickle.loads(data)
#     win.blit(data_variable.surface, (0, 0))
#     pygame.display.flip()
#
# print("finish")
import socket
import pickle
import pygame


class Test:
    def __init__(self, surface):
        self.surface = surface
        self.name = "Test"

    def __getstate__(self):
        state = self.__dict__.copy()
        surface = state.pop("surface")
        state["surface_string"] = (pygame.image.tostring(surface, "RGB"), surface.get_size())
        return state

    def __setstate__(self, state):
        surface_string, size = state.pop("surface_string")
        state["surface"] = pygame.image.fromstring(surface_string, size, "RGB")
        self.__dict__.update(state)


W = 1000
H = 700

pygame.display.set_caption('client')
HEADERSIZE = 10

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 5151))

win = pygame.display.set_mode((W, H))

while True:
    full_msg = b''
    new_msg = True
    while True:
        events = pygame.event.get()
        for event in events:
            pass
        msg = s.recv(16)
        if new_msg:
            print("new msg len:",msg[:HEADERSIZE])
            msglen = int(msg[:HEADERSIZE])
            new_msg = False

        print(f"full message length: {msglen}")

        full_msg += msg

        print(len(full_msg))

        if len(full_msg)-HEADERSIZE == msglen:
            data_variable = (pickle.loads(full_msg[HEADERSIZE:]))
            new_msg = True
            full_msg = b""
            pygame.image.save(data_variable.surface, 'surface.png')
            win.blit(data_variable.surface, (0, 0))
            pygame.display.flip()



# data_string = pickle.dumps(variable)
# s.send(data_string)

# data = conn.recv(4096)
# data_variable = pickle.loads(data)


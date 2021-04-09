import random
import time
import socket
import select
import warnings
import json
from Engine.base_sprites import BaseSprite, player
from common_sprites import Tank, Color, W, H, ts
from Engine.structures import Vector2
from Engine.base_control import wasd
from pygame import K_SPACE
from pygame import Color as pg_color

player.mute = True


def merge_dicts(a: dict, b: dict):
    return {**a, **b}


class Message:
    messages_to_send = []

    def __init__(self, socket_, message):
        self.socket = socket_
        self.message = message
        self.messages_to_send.append(self)

    def send(self):
        self.socket.send(self.message)
        self.messages_to_send.remove(self)

    @classmethod
    def remove_messages_to(cls, socket_):
        cls.messages_to_send = [msg for msg in cls.messages_to_send if not msg.socket == socket_]


class FalseDict(dict):
    """
    Dictionary that returns false instead of raising KeyError if key is not found
    """

    def __getitem__(self, item):
        try:
            return super(FalseDict, self).__getitem__(item)
        except KeyError:
            return False


class User:
    users_list = {}

    @property
    def current_keys(self):
        return [i for i in self.active_keys if self.active_keys[i]]

    def __init__(self, socket_, address):
        self.socket = socket_
        self.address = address
        self.users_list[self.socket] = self
        self.attributes = {}
        self.active_keys = FalseDict()

    def disconnect(self):
        self.users_list.pop(self.socket)
        self.socket.close()

    def __hash__(self):
        return self.address.__hash__()

    def add_attribute(self, value, protected, name):
        self.attributes[name] = Attribute(value, protected, name)

    def set_attribute(self, name, value):
        self.attributes[name].set_value(value)

    def set_keys(self, keys: dict):
        self.active_keys = keys

    def __getattr__(self, item):
        try:
            return super(User, self).__getattr__(item)
        except AttributeError:
            return self.attributes[item].value

    def replace(self, user_class: type, **kwargs):
        new = user_class(self.socket, self.address, **kwargs)
        new.set_keys(self.active_keys)
        self.users_list[self.socket] = new
        del self


class Attribute:
    def __init__(self, value, protected, name, convert_from_string=lambda x: x):
        self.value = value
        self.protected = protected
        self.name = name
        self.converter = convert_from_string

    def set_value(self, value, override_permission):
        if override_permission or not self.protected:
            self.value = self.converter(value)


class ExampleUser(User):
    def __init__(self, socket_, address, *, username):
        super(ExampleUser, self).__init__(socket_, address)
        self.add_attribute(username, False, 'username')
        # self.add_attribute(number, False, 'username')


class SingleShotTimer:
    inf = float('inf')
    timers_list = []

    def __init__(self, function):
        self.timer = self.inf
        self.activated = False
        self.function = function
        self.timers_list.append(self)

    def activate(self, ms):
        self.timer = ms
        self.activated = True

    def reset(self):
        self.timer = self.inf
        self.activated = False

    def update(self, elapsed):
        if self.activated:
            self.timer -= elapsed
            if self.timer <= 0:
                self.function()
                self.timer = 0
                self.timers_list.remove(self)

    def active(self):
        return self.activated

    def __bool__(self):
        return self.active()

    @classmethod
    def update_all(cls, elapsed):
        for timer in cls.timers_list:
            timer.update()


class CommandServer:
    TICKS_PER_SECOND = 60
    PORT = 35241
    IP = "0.0.0.0"

    open_client_sockets = []

    commands = {}

    instance = None

    is_server = True

    def __init__(self):
        CommandServer.instance = self
        self.server_socket = socket.socket()
        self.server_socket.setblocking(False)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen(1000)
        print("yeah")
        BaseSprite.set_server(self)
        self.running = 1
        self.loop()

    def loop(self):
        while self.running:
            print("tick")
            start_time = time.time()
            self.tick()
            time.sleep(1 / self.TICKS_PER_SECOND)
            SingleShotTimer.update_all((time.time() - start_time) * 1000)

            # for user in User.users_list.values():
            #     print(user.current_keys)

    def tick(self):
        read_list, write_list, _ = select.select([self.server_socket] + self.open_client_sockets,
                                                 self.open_client_sockets, [])
        for notified_socket in read_list:
            if notified_socket is self.server_socket:
                self.receive_connection()
            else:
                connected = self.handle_request(notified_socket)
                if not connected:
                    self.disconnect_user(User.users_list[notified_socket])

        self.send_waiting_messages(write_list)

    def receive_connection(self):
        client_socket, client_address = self.server_socket.accept()
        self.open_client_sockets.append(client_socket)
        User(client_socket, client_address)

    def handle_request(self, client_socket):
        try:
            data = bytearray()
            while True:
                try:
                    new = client_socket.recv(4069)
                    if new:
                        data.extend(new)
                    else:
                        break
                except BlockingIOError:
                    break

            if not data:
                print("empty message...")
                return False

            requests = self.smart_split(data.decode(), '\n')
            for request in requests:
                command, kwargs = self.split_message(request)
                self.commands[command](self, User.users_list[client_socket], kwargs)
        except Exception as e:
            warnings.warn("Something broken\n " + repr(e))
            print(command, kwargs)
            print(self.commands[command](self, User.users_list[client_socket], kwargs))
            return False
        return True

    def disconnect_user(self, user: User):
        self.open_client_sockets.remove(user.socket)
        Message.remove_messages_to(user.socket)
        user.disconnect()

    # commands:
    @classmethod
    def command(cls, name=None):
        if callable(name):  # called without parenthesis
            f = name
            cls.commands[f.__name__] = f
            return f

        def inner(f):
            cls.commands[name or f.__name__] = f
            return f

        return inner

    @staticmethod
    def send_waiting_messages(write_list):
        for message in Message.messages_to_send:
            if message.socket in write_list:
                message.send()

    @staticmethod
    def format_string(string):
        r"""Replaces %, & and = with \%, \& and \= respectively"""
        return str(string).replace('%', r'\%').replace('&', r'\&').replace('=', r'\=')

    @classmethod
    def build_packet(cls, command: str, **parameters):
        return cls.format_string(command).encode() + (b'?' if parameters else b'') + ('&'.join(
            ['{}={}'.format(cls.format_string(param), cls.format_string(val))
             for param, val in parameters.items()])).encode() + b'\n'

    @classmethod
    def split_message(cls, request: str):
        command, *arguments = cls.smart_split(request, '?')
        if arguments:
            args = [cls.smart_split(i, '=') for i in cls.smart_split(arguments[0], '&')]
            for arg in args:
                if len(arg) == 1:  # only argument but not value, assign default value.
                    arg.append('')
            kwargs = dict(args)
        else:
            kwargs = {}
        return command, kwargs

    @staticmethod
    def smart_split(string, separator, saver='\\'):
        """Split string by the separator, as long as saver is not present before the separator.
        for example: string='Hello0Dear0W\0rld, separator='0', saver='\' returns ['Hello', 'Dear', 'W0rld']"""
        splited = string.split(separator)
        new_list = []
        i = 0
        while i < len(splited):
            item = splited[i]
            if item:
                if item[-1] == saver and not i + 1 == len(splited):  # merge it with the next item
                    item = item[:-1]
                    item += separator + splited[i + 1]
                    i += 1
                new_list.append(item)
            i += 1

        return new_list

    @staticmethod
    def encode_list(args):
        return ','.join(str(arg).replace(',', r'\,') for arg in args)

    @classmethod
    def decode_list(cls, lst):
        return cls.smart_split(lst, ',')

    def send_message(self, socket_, command: str, **parameters):
        self.send_packet(socket_, self.build_packet(command, **parameters))

    @staticmethod
    def send_packet(socket_, packet):
        Message(socket_, packet)

    def send_all(self, command: str, exceptions=(), *, user_exception=None, **parameters):
        packet = self.build_packet(command, **parameters)
        for sock in self.open_client_sockets:
            if exceptions and sock in exceptions:
                continue

            user = User.users_list[sock]
            Message(sock, packet if ((user_exception is None) or (user not in user_exception)) else
            self.build_packet(command, **self.merge_kwargs(user_exception, user, parameters)))
        return packet

    @staticmethod
    def merge_kwargs(user_exception, user, kwargs):
        if isinstance(user_exception, dict) and user in user_exception:
            return {**kwargs, **user_exception[user]}
        return kwargs


class Server(CommandServer):
    """
    Template:

    @CommandServer.command('protocol_command')
    def function_name(self, user: User, kwargs):
        value = kwargs['key']
        Message(user.socket, self.build_packet('command_name', key1=value1, key2=value2))
    """

    created_sprites = bytearray()

    # commands:
    @CommandServer.command('Connect')
    def connect(self, user: User, kwargs):
        """
        Template:
        user.replace(ExampleUser, **kwargs)
        """
        print('sending create', self.created_sprites)
        user.socket.send(self.created_sprites)

        self.user = user

        self.sprite = self.create_sprite(Tank, user,
                                         init_direction=Vector2.Unit(random.choice(Tank.possible_angles)),
                                         position=Vector2.Cartesian(random.randint(ts, W - ts),
                                                                    random.randint(ts, H-ts)),
                                         control_keys=wasd,
                                         shoot_key=K_SPACE,
                                         color=Color.black,
                                         health_bar_positive_color=pg_color('green'),
                                         health_bar_negative_color=pg_color('red'),
                                         user_exception={user: {'color': Color.green}}
                                         )

    @CommandServer.command('Disconnect')
    def disconnect(self, user: User, kwargs):
        user.disconnect()

    @CommandServer.command('KeyChange')
    def key_change(self, user: User, kwargs):
        key_number = kwargs['keyNumber']
        pressed = kwargs['isPressed']
        # print("key change", key_number, pressed)
        user.active_keys[int(key_number)] = int(pressed)

    @CommandServer.command('SetAttr')
    def set_attribute(self, user: User, kwargs):
        attr = kwargs['attr']
        value = kwargs['value']

        user.set_attribute(attr, value)

    # /commands
    # def create_sprite(self, cls, controller: User = None, *, user_exception=None, **kwargs):
    #     if user_exception is None:
    #         user_exception = {}
    #     sprite = cls(**kwargs)
    #     kwargs = cls.encode_creation(**kwargs)
    #     packet = self.send_all('Create', id=sprite.id, classId=cls.id, control=0,
    #                            exceptions=(controller.socket,) if controller is not None else (),
    #                            user_exception=user_exception, **kwargs)
    #
    #     self.created_sprites.extend(packet)
    #     if controller is not None:
    #         self.send_message(controller.socket, 'Create', id=sprite.id, classId=cls.id, control=1,
    #                           **self.merge_kwargs(user_exception, controller, kwargs)
    #                           )
    #     sprite.set_user(controller)
    #     return sprite

    def create_sprite(self, cls, controller: User = None, *, user_exception=None, **kwargs):
        if user_exception is None:
            user_exception = {}
        if controller is not None:
            old = user_exception.get(controller, {})
            user_exception[controller] = {**{'control': 1}, **old}

        print(user_exception)
        sprite = cls(**kwargs)
        default_kwargs = cls.encode_creation(**kwargs)
        kwargs_dict = {'id': sprite.id, 'classId': cls.id, 'control': 0, **default_kwargs}

        default_packet = self.build_packet('Create', **kwargs_dict)
        for user in User.users_list.values():
            packet = default_packet
            if user in user_exception:
                packet = self.build_packet('Create', **{**kwargs_dict,
                                                        **merge_dicts(
                                                            user_exception[user]
                    ,cls.encode_creation(**user_exception[user]))})
                print('exception1!!!', packet)
            self.send_packet(user.socket, packet)

        self.created_sprites.extend(default_packet)

        sprite.set_user(controller)
        return sprite

    def send_sprite_update(self, sprite):
        kwargs = sprite.encode()

        # try:
        #     print(self.user.current_keys)
        # except AttributeError:
        #     pass
        # try:
        #     print(sprite.user)
        # except AttributeError:
        #     pass
        self.send_all('Update', id=sprite.id, **kwargs)

    def update_all(self, sprite_list):
        for sprite in sprite_list:
            if sprite.id is not None:
                self.send_sprite_update(sprite)

    def tick(self):
        self.update_all(BaseSprite.sprites_list)
        super(Server, self).tick()


if __name__ == '__main__':
    Server()

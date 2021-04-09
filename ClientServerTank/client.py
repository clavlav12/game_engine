from threading import Thread
import socket
import select
import warnings
from Engine import base_sprites


class CommandClient(Thread):
    SERVER_PORT = 35241
    IP = "127.0.0.1"
    try:
        with open('ip.txt', 'r') as file:
            IP = file.read().strip()
    except:
        open('ip.txt', 'w').close()
    # IP = "212.76.116.100"
    # IP = "31.44.141.250"
    commands = {}

    is_server = False

    def __init__(self):
        super(CommandClient, self).__init__()
        self.socket = None
        base_sprites.BaseSprite.set_server(self)

    def run(self):
        self.connected = self.connect_server()
        while self.connected:
            read_list = select.select([self.socket], [], [], 1)[0]
            if read_list:
                self.handle_request()
        # print("finished")
        self.socket.close()
        # self.disconnect_and_quit(False)

    def connect_server(self):
        self.socket = socket.socket()
        self.socket.settimeout(10)
        try:
            ip = self.IP
            print("connecting")
            self.socket.connect((ip, self.SERVER_PORT))
            print("connected")
            self.connect()
            self.socket.setblocking(False)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return True
        except (Exception, socket.timeout) as e:
            raise e
            return False

    def disconnect_and_quit(self):
        try:
            self.socket.send(self.build_packet('Disconnect'))
            self.connected = False
        except Exception as e:
            print(e)
            pass

    def handle_request(self):
        try:
            data = bytearray()
            while True:
                try:
                    new = self.socket.recv(4069)
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
                self.commands[command](self, kwargs)
        except Exception as e:
            raise  e
            # warnings.warn("Something broken\n " + repr(e))
            return False
        return True

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
            a = [cls.smart_split(i, '=') for i in cls.smart_split(arguments[0], '&')]
            kwargs = dict(a)
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
                if item[-1] == saver and not i+1 == len(splited):  # merge it with the next item
                    item = item[:-1]
                    item += separator + splited[i+1]
                    i += 1
                new_list.append(item)
            i += 1

        return new_list

    @staticmethod
    def encode_list(args):
        return ','.join(arg.replace(',', r'\,') for arg in args)

    @classmethod
    def decode_list(cls, lst):
        return cls.smart_split(lst, ',')

    def send_message(self, command: str, **parameters):
        self.socket.send(self.build_packet(command, **parameters))

    def connect(self):
        print("sent connect")
        self.send_message('Connect')


class FalseDict(dict):
    """
    Dictionary that returns false instead of raising KeyError if key is not found
    """

    def __getitem__(self, item):
        try:
            return super(FalseDict, self).__getitem__(item)
        except KeyError:
            return False


class OtherUser:
    def __init__(self):
        self.active_keys = FalseDict()

    def __bool__(self):
        return False


class Client(CommandClient):
    def key_event(self, key: int, pressed: bool):
        self.send_message('KeyChange', keyNumber=key, isPressed=pressed)

    def connect(self):
        self.send_message('Connect')

    @CommandClient.command('Update')
    def update_sprite(self, kwargs):
        id_ = kwargs.pop('id')
        try:
            base_sprites.BaseSprite.sprites_by_id[id_].decode_update(**kwargs)
        except KeyError as e:
            print("sprite is not created yet", e)

    @CommandClient.command('Create')
    def create_sprite(self, kwargs):
        id_ = kwargs.pop('id')
        class_id = kwargs.pop('classId')
        controlled = kwargs.pop('control')

        cls = base_sprites.BaseSprite.get_sprite_class(class_id)
        kwargs = cls.decode_creation(**kwargs)
        new = cls.create_from_kwargs(id_=id_, **kwargs)
        if isinstance(new, base_sprites.BaseSprite):
            new.set_id(int(id_))
            if not int(controlled):
                new.set_user(OtherUser())


# @CommandClient.command

from abc import ABC, abstractmethod


def abstract_attribute(f):
    f = abstractmethod(f)
    f = property(f)
    return f


class NetworkProtocol(ABC):
    HOST_PORT = 35421

    def __init__(self):
        self.__class__.instance = self

    @abstract_attribute
    def HOST_IP(self) -> str:
        pass

    @abstract_attribute
    def instance(self):
        return None

    @abstract_attribute
    def commands(self) -> dict:
        pass

    @abstract_attribute
    def is_server(self) -> bool:
        pass

    @abstractmethod
    def call_command(self, command, kwargs, socket):
        pass

    def handle_request(self, socket):
        try:
            data = bytearray()
            while True:
                try:
                    new = socket.recv(4069)
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
                self.call_command(command, kwargs,  socket)

        except Exception as e:
            raise e
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
            args = [cls.apply_default(i, '=') for i in cls.smart_split(arguments[0], '&')]
            kwargs = dict(args)
        else:
            kwargs = {}
        return command, kwargs

    @classmethod
    def apply_default(cls, string, separator):
        """
        Separate string of type arg=value to (arg, value), and sets value to empty string
        if value is not presented
        """

        split = cls.smart_split(string, '=')
        if len(split) == 1:
            split.append('')
        return split

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
        return ','.join(arg.replace(',', r'\,') for arg in args)

    @classmethod
    def decode_list(cls, lst):
        return cls.smart_split(lst, ',')


from server import CommandServer


class MyServer(CommandServer):

    @CommandServer.command
    def add(self, user, kwargs):
        self.send_message(user, 'result', result=int(kwargs['a']) + int(kwargs['b']))


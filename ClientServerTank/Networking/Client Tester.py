from client import CommandClient


class MyClient(CommandClient):

    @CommandClient.command
    def result(self, kwargs):
        print(kwargs['result'])

a = MyClient()
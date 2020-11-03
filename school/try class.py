
class A:
    def __init__(self, value):
        self.value = value
        self.a = B(self.cool)

    def cool(self):
        self.value += 1


class B:
    def __init__(self, function):
        self.function = function

    def callme(self):
        self.function()

a = A(5)
a.a.callme()
print(a.value)


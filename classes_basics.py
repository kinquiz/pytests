# classes basics


class Dog:
    species = "canis familiaris"

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return self.name + " says woof"

    def birthday(self):
        self.age += 1


rex = Dog("Rex", 3)
print(rex.bark())
assert rex.bark() == "Rex says woof"
assert rex.species == "canis familiaris"

rex.birthday()
assert rex.age == 4

fido = Dog("Fido", 1)
assert fido.species == rex.species
assert fido.name != rex.name

print(rex)


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)


p1 = Point(1, 2)
p2 = Point(3, 4)
print(p1)
print(repr(p2))
assert str(p1) == "(1, 2)"
assert repr(p2) == "Point(3, 4)"
assert p1 + p2 == Point(4, 6)  # without __eq__ this compares identity
assert p1 != p2  # __ne__ derived from __eq__


class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

    def introduce(self):
        return f"I am {self.name} and I say {self.speak()}"


class Cat(Animal):
    def speak(self):
        return "meow"


class Cow(Animal):
    def __init__(self, name, milk_litres):
        super().__init__(name)
        self.milk_litres = milk_litres

    def speak(self):
        return "moo"


tom = Cat("Tom")
bessie = Cow("Bessie", 20)
assert tom.introduce() == "I am Tom and I say meow"
assert bessie.introduce() == "I am Bessie and I say moo"
assert bessie.milk_litres == 20
assert isinstance(tom, Animal)
assert isinstance(tom, Cat)
assert not isinstance(tom, Cow)

animals = [Cat("A"), Cow("B", 5), Animal("C")]
sounds = [a.speak() for a in animals]
assert sounds == ["meow", "moo", "..."]


class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.history = []

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self.balance += amount
        self.history.append(("deposit", amount))

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("not enough money")
        self.balance -= amount
        self.history.append(("withdraw", amount))

    def __len__(self):
        return len(self.history)


acc = BankAccount("Ann")
acc.deposit(100)
acc.withdraw(30)
assert acc.balance == 70
assert len(acc) == 2

try:
    acc.withdraw(1000)
except ValueError as e:
    print("error:", e)
assert acc.balance == 70


class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius

    @classmethod
    def from_fahrenheit(cls, f):
        return cls((f - 32) * 5 / 9)

    @staticmethod
    def is_freezing(celsius):
        return celsius <= 0

    @property
    def fahrenheit(self):
        return self.celsius * 9 / 5 + 32


t = Temperature.from_fahrenheit(212)
assert t.celsius == 100
assert t.fahrenheit == 212
assert Temperature.is_freezing(-5)

print("classes ok")

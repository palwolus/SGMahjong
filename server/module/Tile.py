class Tile:
    def __init__(self):
        self.type = None


class Character(Tile):
    def __init__(self, number: int):
        super().__init__()
        self.type = 'char'
        self.number = number

    def __repr__(self):
        return 'char_' + str(self.number)


class Dot(Tile):
    def __init__(self, number: int):
        super().__init__()
        self.type = 'dot'
        self.number = number

    def __repr__(self):
        return 'dot_' + str(self.number)


class Bamboo(Tile):
    def __init__(self, number: int):
        super().__init__()
        self.type = 'bamboo'
        self.number = number

    def __repr__(self):
        return 'bamboo_' + str(self.number)


class Big(Tile):
    def __init__(self, name: str):
        super().__init__()
        self.type = 'big'
        self.name = name

    def __repr__(self):
        return self.name


class Flower(Tile):
    def __init__(self, number: int, category: str):
        super().__init__()
        self.type = 'flower'
        self.number = number
        self.category = category

    def __repr__(self):
        return str(self.category) + '_' + str(self.number)


class Animal(Tile):
    def __init__(self, breed: str):
        super().__init__()
        self.type = 'animal'
        self.breed = breed

    def __repr__(self):
        return self.breed

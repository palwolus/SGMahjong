import pygame
import random
import copy


class Tile:
    def __init__(self, name, image, screen_width, screen_height):
        # Call the parent class (Sprite) constructor
        self.name = name
        self.image = image
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rect = None
        self.position = None

    def load_tile(self, type=None, pos=None):
        self.image = pygame.image.load(self.image).convert_alpha()
        self.image = pygame.transform.scale(self.image, (60, 75))
        self.rect = self.image.get_rect()
        self.rect.y = self.screen_height - 75

        if type == 'enemy':
            self.load_enemy_board(pos)
        elif type == 'ffa':
            self.load_ffa()
        elif type == 'board':
            self.load_board()
        elif type == 'possible':
            self.load_possible()
        elif type == 'hu':
            self.load_hu()

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.position:
            self.rect.x = self.position[0]
            self.rect.y = self.position[1]

    def load_hu(self):
        self.image = pygame.transform.scale(self.image, (30, 45))
        self.rect = self.image.get_rect()

    def load_possible(self):
        self.image = pygame.transform.scale(self.image, (40, 55))
        self.rect = self.image.get_rect()

    def load_board(self):
        self.image = pygame.transform.scale(self.image, (40, 55))
        self.rect = self.image.get_rect()

    def load_enemy_board(self, pos=None):
        self.image = pygame.transform.scale(self.image, (30, 45))
        if pos == 'left':
            self.image = pygame.transform.rotate(self.image, -90)
        elif pos == 'right':
            self.image = pygame.transform.rotate(self.image, 90)

        self.rect = self.image.get_rect()

    def load_ffa(self):
        self.image = pygame.transform.scale(self.image, (30, 45))
        self.image = pygame.transform.rotate(self.image, random.randint(-45, 45))
        self.position = [random.randint(70, 800-50), random.randint(70, 415-45-20)]
        self.rect = self.image.get_rect()

    def __repr__(self):
        return self.name

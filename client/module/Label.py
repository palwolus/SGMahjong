import pygame
import random


class Label:
    def __init__(self, text=None, color=None, font_size=None, pos=None, x=None, y=None, auto=True):
        self.text = text
        self.color = color if color else (0, 0, 0)
        self.font_size = font_size if font_size else 30
        self.position = pos if pos else (x, y)
        self.text_obj = None
        self.text_rect = None
        if auto:
            self.update()

    def update(self):
        self.text_obj = pygame.font.SysFont(None, self.font_size).render(self.text, 1, self.color)
        self.text_rect = self.text_obj.get_rect()
        self.text_rect.topleft = self.position

    def change(self):
        self.text = str(random.randint(0, 1000))

    def draw(self, screen):
        screen.blit(self.text_obj, self.text_rect)


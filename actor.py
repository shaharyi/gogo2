import os
from greenlet import greenlet
from pygame.sprite import Sprite
import pygame

from util import log, IMAGE_EXT


class SpriteActor(Sprite):
    def __init__(self, image_file=None, topleft=None, center=None, groups=()):
        super().__init__(*groups)
        image_file = image_file or self.__class__.__name__
        filepath = os.path.join('data', image_file) + '.' + IMAGE_EXT
        log('* loading ' + filepath)
        self.image = pygame.image.load(filepath).convert()
        self.orig_image = self.image.copy()
        location = topleft and dict(topleft=topleft) or center and dict(center=center) or {}
        self.rect = self.image.get_rect(**location)

    def handle_update(self):
        # update() is inherited from Sprite
        self.update()

    def die(self):
        for g in self.groups():
            g.remove(self)
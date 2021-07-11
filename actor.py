from pdb import set_trace
import os
import pickle
from pygame.sprite import Sprite
import pygame

from config import *
from util import log


class SpriteActor(Sprite):
    image_cache = {}

    def __init__(self, image_file=None, topleft=None, center=None, groups=()):
        super().__init__(*groups)
        image_file = image_file or self.__class__.__name__
        self.filepath = os.path.join('data', image_file) + '.' + IMAGE_EXT
        self.image = self.image_cache.get(self.filepath)
        if not self.image:
            log('* loading ' + self.filepath)
            self.image = pygame.image.load(self.filepath)
            if pygame.get_init():
                self.image = self.image.convert()
            self.image_cache[self.filepath] = self.image

        self.orig_image = self.image.copy()
        location = topleft and dict(topleft=topleft) or center and dict(center=center) or {}
        self.rect = self.image.get_rect(**location)
        self.render_props = ['filepath', 'rect']

    def handle_update(self):
        # update() is inherited from Sprite
        self.update()

    def die(self):
        for g in self.groups():
            g.remove(self)

    def get_render_data(self):
        data = [(k, getattr(self, k)) for k in self.render_props]
        return tuple(data)


def serialize_sprites(*groups):
    sprites = [s for sg in groups for s in sg.sprites()]
    data = []
    for s in sprites:
        if isinstance(s, SpriteActor):
            data.append(s.get_render_data())
    return tuple(data)

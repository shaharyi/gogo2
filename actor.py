from pdb import set_trace
import os
import time
from pygame.sprite import Sprite
import pygame

from config import *
from util import log


class SpriteActor(Sprite):
    image_cache = {}

    def __init__(self, image_file=None, topleft=None, center=None, ttl=0, groups=()):
        super().__init__(*groups)
        image_file = image_file or self.__class__.__name__
        self.filepath = os.path.join('data', image_file) + '.' + IMAGE_EXT
        self.image = self.image_cache.get(self.filepath)
        self.ttl = ttl
        self.ttl_callback = self.die
        if not self.image:
            log('* loading ' + self.filepath)
            self.image = pygame.image.load(self.filepath)
            if pygame.get_init():
                self.image = self.image.convert()
            self.image_cache[self.filepath] = self.image

        self.orig_image = self.image.copy()
        s = self.image.get_rect().size
        self.pos = topleft and topleft or (center[0] - s[0], center[1] - s[1])
        tl = tuple(map(round, self.pos))
        self.rect = self.image.get_rect(topleft=tl)
        self._sounds = []
        self.start_time = time.time()
        self.render_props = ['filepath', 'rect', 'sounds']

    @property
    def sounds(self):
        ret = tuple(self._sounds)
        self._sounds = []
        return ret

    def append_sound(self, name):
        self._sounds.append(name)

    def handle_update(self):
        # update() is inherited from Sprite
        self.update()

    def die(self):
        for g in self.groups():
            g.remove(self)

    def get_render_data(self):
        data = [(k, getattr(self, k)) for k in self.render_props]
        return tuple(data)

    def update(self):
        if self.ttl and time.time() - self.start_time >= self.ttl:
            self.ttl_callback()


def serialize_sprites(*groups):
    sprites = [s for sg in groups for s in sg.sprites()]
    data = []
    for s in sprites:
        if isinstance(s, SpriteActor):
            data.append(s.get_render_data())
    return tuple(data)

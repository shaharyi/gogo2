import os
from greenlet import greenlet
import pygame

from util import log, IMAGE_EXT


class Actor:
    def __init__(self, sprite, world=None):
        self.greenlet = greenlet(self.msg_pump)
        self.world = world
        self.sprite = sprite

    def msg_pump(self, data):
        while 1:
            data = self.world.switch()
            self.process_message(data)

    def process_message(self,args):
        method_name= 'handle_'+args[1]
        method= getattr(self.sprite, method_name, None)
        if method is None:
            log('Unknown msg=%s for %s' % (args[1], self.name))
        else:
            method(args)

    def die(self):
        self.world.send( (self.id, "KILLME") )

    def update(self):
        pass


class SpriteActor(pygame.sprite.Sprite):
    def __init__(self, img=None, topleft=None, center=None, world=None, *args):
        super().__init__(*args)
        img = img or self.__class__.__name__
        filepath = os.path.join('data', img) + '.' + IMAGE_EXT
        log('* loading ' + filepath)
        self.image = pygame.image.load(filepath).convert()
        self.orig_image = self.image.copy()
        location = topleft and dict(topleft=topleft) or center and dict(center=center) or {}
        self.rect = self.image.get_rect(**location)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.actor = Actor(self, world)

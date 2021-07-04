import os
from greenlet import greenlet
from pygame.sprite import Sprite
import pygame

from util import log, IMAGE_EXT


class Actor:
    next_id = 0

    def __init__(self, world=None):
        self.id = Actor.next_id
        Actor.next_id += 1
        self.world = world
        self.name = "%s#%d" % (self.__class__.__name__, self.id)
        if world:
            self.greenlet = greenlet(self.msg_pump)

    def msg_pump(self, data):
        while 1:
            data = self.world.switch()
            self.process_message(data)

    def process_message(self,args):
        method_name = 'handle_'+args[1]
        method = getattr(self, method_name, None)
        if method is None:
            log('Unknown msg=%s for %s' % (args[1], self.name))
        else:
            method(args)

    def die(self):
        if self.world:
            self.world.send((self.id, "KILLME"))

    def update(self):
        pass


class SpriteActor(Sprite, Actor):
    def __init__(self, image_file=None, topleft=None, center=None, world=None, groups=()):
        super().__init__(*groups)
        Actor.__init__(self)
        image_file = image_file or self.__class__.__name__
        filepath = os.path.join('data', image_file) + '.' + IMAGE_EXT
        log('* loading ' + filepath)
        self.image = pygame.image.load(filepath).convert()
        self.orig_image = self.image.copy()
        location = topleft and dict(topleft=topleft) or center and dict(center=center) or {}
        self.rect = self.image.get_rect(**location)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.actor = world and Actor(self, world)

    def die(self):
        super().die()
        for g in self.groups():
            g.remove(self)
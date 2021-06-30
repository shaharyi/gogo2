from greenlet import greenlet

import pygame
import util


class Actor:
    def __init__(self):
        self.greenlet = greenlet(self.process_message)

    def process_message(self):
        while 1:
            self.process_message_action(self.greenlet.receive())

    def process_message_action(self,args):
        method_name= 'handle_'+args[1]
        method= getattr(self, method_name, None)
        if method is None:
            util.log('Unknown msg=%s for %s' % (args[1], self.name))
        else:
            method(args)

    def die(self):
        self.world.send( (self.id, "KILLME") )

    def update(self):
        pass


class SpriteActor(Actor, pygame.sprite.Sprite):
    def __init__(self, img=None, topleft=None, center=None):
        pygame.sprite.Sprite.__init__(self)
        img = img or self.__class__.__name__ + '.png'
        self.surf = pygame.image.load(img).convert()
        location = topleft and {topleft:topleft} or center and {center:center} or {}
        self.rect = self.surf.get_rect(**location)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        Actor.__init__(self)

import math

from pygame import K_RIGHT, K_LEFT, K_DOWN, K_UP, K_SPACE, K_m
import pygame

from util import *
from sample_actors import BasicRobot, Mine, Bullet

THRUST = 5
FRICTION = 3
ANGLE_DELTA = 5

# player 1 keyboard mapping
p1_key_down_reversed = dict(left=K_RIGHT, right=K_LEFT, forward=K_UP, backward=K_DOWN, shoot=K_SPACE, drop_mine=K_m)
p1_key_down = {v: k for k, v in p1_key_down_reversed.items()}
p1_key_up_reversed = dict(center=K_RIGHT, center_=K_LEFT, stop=K_UP, stop_=K_DOWN)
p1_key_up = {v: k.strip('_') for k, v in p1_key_up_reversed.items()}
mappings_down = [p1_key_down]
mappings_up = [p1_key_up]


class PlayerActor(BasicRobot):
    """Player sprite

    Respon:
    Follows the physical model of a amusement colliding cars, with friction and
    thrust (-5, 0 or 5).
    It counts active players (nplayers) to load the right sprite image.

    Collab:
    Receive INPUT msgs (originated at Client Display, forwarded by Server) and change velocity/angle accordingly.
    """
    nplayers = 0

    def __init__(self, location, score, number=0):
        # location = location or (PlayerActor.nplayers%2 and 50  or World._singleton.width-50, 250)
        super().__init__(location=location)
        self.score = score
        self.angle = 90
        self.angle_d = 0
        self.velocity = 0
        self.hitpoints = 20
        self.thrust = 0
        self.image_file = self.__class__.__name__ + str(number) + IMAGE_EXT
        self.kmap_down = {k: getattr(self, v) for k, v in mappings_down[number]}
        self.kmap_up = {k: getattr(self, v) for k, v in mappings_up[number]}

    def process_input(self, event):
        if event.type == pygame.KEYDOWN:
            self.kmap_down[event.key]()
        elif event.type == pygame.KEYUP:
            self.kmap_up[event.key]()

    def drop_mine(self):
        mineDistance =  self.rect.h
        v = [math.cos(math.radians(self.angle+90)),
             math.sin(math.radians(self.angle+90))]
        loc= [0,0]
        for d in (0,1):
            v[d] *= mineDistance
            loc[d] = self.rect[d+2] + self.rect[d+2]/2 + v[d]
        Mine(center=loc)

    def shoot(self):
        distance =  self.rect.h
        v = [math.cos(math.radians(self.angle+90)),
             math.sin(math.radians(self.angle+90))]
        loc= [0,0]
        for d in (0,1):
            v[d] *= distance
            loc[d] = self.rect[d+2] + self.rect[d+2]/2 - v[d]
        Bullet(shooter=self, center=loc, angle=self.angle)

    def killed_actor(self, _target):
        "Called when we kill another player or robot"
        self.score.value += _target.__class__.__name__=='PlayerActor' and 100 or 10

    def forward(self):
        self.thrust = THRUST

    def backward(self):
        self.thrust = THRUST

    def stop(self):
        self.thrust = 0

    def right(self):
        self.angle_d = +ANGLE_DELTA

    def left(self):
        self.angle_d = -ANGLE_DELTA

    def center(self):
        self.angle_d = 0

    def bump(self, damage=0):
        # bump wall or another robot
        self.rect = self.old_rect
        self.velocity = 0
        if damage: self.take_damage(damage)

    def update(self):
        d_v = self.thrust - sign(self.velocity)*FRICTION
        self.velocity += abs(self.velocity+d_v)<=self.MAX_VELOCITY and d_v or 0
        self.angle += self.angle_d
        self.angle = self.angle<0 and self.angle%-360 or self.angle%360
        super().update()

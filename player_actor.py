from pdb import set_trace
import math

from pygame import K_RIGHT, K_LEFT, K_DOWN, K_UP, K_SPACE, K_m, KEYDOWN, KEYUP

from util import *
from sample_actors import Robot, Mine, Bullet

THRUST = 1.5
FRICTION = 1
ANGLE_DELTA = 5*math.pi/180
twoPI = 2*math.pi
halfPI = math.pi/2

# player 1 keyboard mapping
p1_key_down_reversed = dict(left=K_LEFT, right=K_RIGHT, forward=K_UP, backward=K_DOWN, shoot=K_SPACE, drop_mine=K_m)
p1_key_down = {v: k for k, v in p1_key_down_reversed.items()}
p1_key_up_reversed = dict(center=K_RIGHT, center_=K_LEFT, stop=K_UP, stop_=K_DOWN)
p1_key_up = {v: k.strip('_') for k, v in p1_key_up_reversed.items()}

# for now, we only have player 1 mapping
mappings = {KEYDOWN: [p1_key_down,], KEYUP: [p1_key_up,]}


class PlayerActor(Robot):
    """Player sprite

    Respon:
    Follows the physical model of a amusement colliding cars, with friction and
    thrust (-5, 0 or 5).
    It counts active players (nplayers) to load the right sprite image.

    Collab:
    Receive INPUT msgs (originated at Client Display, forwarded by Server) and change velocity/angle accordingly.
    """
    nplayers = 0
    MAX_VELOCITY = 10

    def __init__(self, topleft, score, number=0, groups=()):
        # location = location or (PlayerActor.nplayers%2 and 50  or World._singleton.width-50, 250)
        image_file = self.__class__.__name__ + str(number+1)
        super().__init__(topleft=topleft, image_file=image_file, velocity=0, angle_deg=90, groups=groups)
        self.score = score
        self.angle_d = 0
        self.hitpoints = 20
        self.thrust = 0
        kmap_down = {k: getattr(self, v) for k, v in mappings[KEYDOWN][number].items()}
        kmap_up = {k: getattr(self, v) for k, v in mappings[KEYUP][number].items()}
        self.kmap = {KEYDOWN: kmap_down, KEYUP: kmap_up}

    def process_input(self, event):
        mapping = self.kmap.get(event.type)
        action = mapping and mapping.get(event.key)
        action and action()

    def drop_mine(self):
        center = self.rect.center
        d = self.rect.h
        v = [d*math.cos(self.angle + halfPI) + center[0],
             d*math.sin(self.angle + halfPI) + center[1]]
        Mine(center=v, groups=self.groups())

    def shoot(self):
        center = self.rect.center
        d = self.rect.h
        v = [center[0] - d*math.cos(self.angle + halfPI),
             center[1] - d*math.sin(self.angle + halfPI)]
        Bullet(shooter=self, center=v, angle=self.angle, groups=self.groups())

    def killed_actor(self, _target):
        "Called when we kill another player or robot"
        self.score.value += _target.__class__.__name__=='PlayerActor' and 100 or 10

    def forward(self):
        self.thrust = THRUST

    def backward(self):
        self.thrust = -THRUST

    def stop(self):
        self.thrust = 0

    def right(self):
        self.angle_d = -ANGLE_DELTA

    def left(self):
        self.angle_d = +ANGLE_DELTA

    def center(self):
        self.angle_d = 0

    def update(self):
        d_v = self.thrust - sign(self.velocity)*FRICTION
        self.velocity += abs(self.velocity+d_v)<=self.MAX_VELOCITY and d_v or 0
        self.angle += self.angle_d
        self.angle = self.angle<0 and self.angle%-twoPI or self.angle%twoPI
        super().update()

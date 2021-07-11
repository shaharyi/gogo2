from pdb import set_trace
from math import sin, cos, pi

from pygame import K_RIGHT, K_LEFT, K_DOWN, K_UP, K_SPACE, K_m, KEYDOWN, KEYUP

from util import sign
from sample_actors import Robot, Mine, Bullet, Score, MinedropperRobot, BasicRobot

THRUST = 1.5
FRICTION = 1
ANGLE_DELTA = 5*pi/180

# player 1 keyboard mapping
p1_key_down_reversed = dict(left=K_LEFT, right=K_RIGHT, forward=K_UP, backward=K_DOWN, shoot=K_SPACE, drop_mine=K_m)
p1_key_down = {v: k for k, v in p1_key_down_reversed.items()}
p1_key_up_reversed = dict(center=K_RIGHT, center_=K_LEFT, stop=K_UP, stop_=K_DOWN)
p1_key_up = {v: k.strip('_') for k, v in p1_key_up_reversed.items()}

# for now, we only have player 1 mapping
mappings = {KEYDOWN: [p1_key_down, ], KEYUP: [p1_key_up, ]}


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

    def __init__(self, topleft, groups=()):
        # location = location or (PlayerActor.nplayers%2 and 50  or World._singleton.width-50, 250)
        self.nplayers += 1
        image_file = self.__class__.__name__ + str(self.nplayers)
        super().__init__(topleft=topleft, image_file=image_file, groups=groups)
        score_loc = (50, 50 * self.nplayers)
        self.score = Score(topleft=score_loc, groups=groups)
        self.angle_d = 0
        self.hitpoints = 20
        self.thrust = 0
        kmap_down = {k: getattr(self, v) for k, v in mappings[KEYDOWN][self.nplayers-1].items()}
        kmap_up = {k: getattr(self, v) for k, v in mappings[KEYUP][self.nplayers-1].items()}
        self.kmap = {KEYDOWN: kmap_down, KEYUP: kmap_up}

    def process_input(self, event_data):
        event_type, event_key = event_data
        mapping = self.kmap.get(event_type)
        action = mapping and mapping.get(event_key)
        action and action()

    def drop_mine(self):
        center = self.rect.center
        d = self.rect.h
        v = [center[0] - d * cos(self.angle),
             center[1] + d * sin(self.angle)]
        Mine(center=v, groups=self.groups())

    def shoot(self):
        center = self.rect.center
        d = self.rect.h/4
        v = [center[0] + d * cos(self.angle),
             center[1] - d * sin(self.angle)]
        Bullet(shooter=self, center=v, angle=self.angle, groups=self.groups())

    def killed_actor(self, _target):
        "Called when we kill another player or robot"
        s = {BasicRobot: 10, MinedropperRobot: 30, PlayerActor: 100}
        add = s.get(_target.__class__, 0)
        self.score.value += add

    def forward(self):
        self.thrust = THRUST

    def backward(self):
        self.thrust = -THRUST

    def stop(self):
        self.thrust = 0

    def right(self):
        self.angle_d = -ANGLE_DELTA

    def left(self):
        print('LEFT')
        self.angle_d = +ANGLE_DELTA

    def center(self):
        print('CENTER')
        self.angle_d = 0

    def update(self):
        d_v = self.thrust - sign(self.velocity)*FRICTION
        self.velocity += abs(self.velocity+d_v)<=self.MAX_VELOCITY and d_v or 0
        self.angle += self.angle_d
        self.angle = self.angle<0 and self.angle%(-2*pi) or self.angle%(2*pi)
        super().update()

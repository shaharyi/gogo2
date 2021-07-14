from pdb import set_trace
from math import degrees, radians, cos, sin, pi
import time
import random

import pygame

import util
from actor import SpriteActor
from config import *


class VectorActor(SpriteActor):
    def __init__(self, image_angle_deg=0, angle=0, velocity=0, groups=(), *args, **kwargs):
        super().__init__(groups=groups, *args, **kwargs)
        self.angle = angle
        self.orig_image_angle = radians(image_angle_deg)
        self.image_angle = self.orig_image_angle
        self.velocity = velocity
        self.render_props += ['angle', 'orig_image_angle']
        self.rotate()

    def rotate(self):
        if self.image_angle != self.angle:
            rot_deg = degrees(self.angle - self.orig_image_angle)
            self.image = util.rotate(self.orig_image, rot_deg)
            self.image_angle = self.angle

    def update(self):
        (a, m) = self.angle, self.velocity
        (dx, dy) = (m * cos(a), m * sin(a))
        self.rect = self.rect.move(dx, -dy)
        self.rotate()

    def bump(self):
        pass


class Robot(VectorActor):
    """Can take damage of bump() until hitpoints is down to zero.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hitpoints = 1
        self.old_rect = self.rect  # enable step-back on bumping an object

    def take_damage(self, damage):
        self.hitpoints -= damage
        if self.hitpoints <= 0:
            Explosion(center=self.rect.center, angle=self.angle, groups=self.groups())
            self.die()

    def bump(self, damage=0):
        self.rect = self.old_rect
        self.velocity = 0
        if damage:
            self.take_damage(damage)

    def update(self):
        self.old_rect = self.rect
        super().update()


class BasicRobot(Robot):
    """A dumb robot that goes in circles
    """
    def __init__(self, velocity=2, image_angle_deg=ORIG_ANGLE, *args, **kwargs):
        super().__init__(velocity=velocity, image_angle_deg=image_angle_deg, *args, **kwargs)

    def bump(self, damage=0):
        self.rect = self.old_rect
        self.angle += radians(73)
        if self.angle >= 4*pi:
            self.angle -= 4*pi
        if damage:
            self.take_damage(damage)

    def update(self):
        self.angle += radians(1)
        if self.angle >= 4*pi:
            self.angle -= 4*pi
        super().update()


class Explosion(VectorActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = time.time()
        self.last_rotate = 0.0
        self.physical = False

    def update(self):
        super().update()
        now = time.time()
        if not self.last_rotate or now - self.last_rotate > 0.1:
            self.last_rotate = now
            self.angle = random.random() * 2 * pi
        if now - self.time >= + 3.0:
            self.die()


class Score(SpriteActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.physical = False
        self.value = 0
        self.showing = -1
        self.font = pygame.font.SysFont('serif', 24)

    def update(self):
        if self.value != self.showing:
            # render(text, antialias, color (RGBA), background=None): return Surface
            t = "%5d" % self.value
            text = self.font.render(t, 1, (0, 0, 0, 0), (200, 200, 200))
            self.image.blit(text, (0, 0))  # in location (0,0)
            self.showing = self.value


class Mine(SpriteActor):
    def __init__(self, center, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hitpoints = 1
        self.rect.center = center

    def bump(self):  # dropped over a wall
        self.die()


class Bullet(VectorActor):
    def __init__(self, shooter, center, angle, *args, **kwargs):
        super().__init__(velocity=2, center=center, angle=angle, *args, **kwargs)
        self.shooter = shooter
        self.damage = 1
        self.hitpoints = 1

    def bounce(self, wall):
        if isinstance(wall, VWall):
            self.angle = pi - self.angle
        elif isinstance(wall, HWall):
            self.angle = -self.angle

    def bump(self, damage=0):  # hit a mine or a wall
        self.die()


class Wall(SpriteActor):
    def __init__(self, topleft, groups, angle=0, *args, **kwargs):
        super().__init__(topleft=topleft, groups=groups, *args, **kwargs)
        angle = angle


class VWall(Wall):
    pass


class HWall(Wall):
    pass


class MinedropperRobot(Robot):
    def __init__(self, velocity=0.1, image_angle_deg=ORIG_ANGLE, *args, **kwargs):
        super().__init__(velocity=velocity, image_angle_deg=image_angle_deg, *args, **kwargs)
        self.hitpoints = 5
        self.delta = 0.0
        self.deltaDirection = "up"
        self.nextMine = 0.0

    def update(self):
        super().update()
        if self.deltaDirection == "up":
            self.delta += radians(2)
            if self.delta > radians(15):
                self.delta = radians(15)
                self.deltaDirection = "down"
        else:
            self.delta -= radians(2)
            if self.delta < radians(-15):
                self.delta = radians(-15)
                self.deltaDirection = "up"
        if self.nextMine <= time.time():
            self.nextMine = time.time() + 5 * random.random()
            center = self.rect.center
            d = self.rect.h
            v = [center[0] - d * cos(self.angle),
                 center[1] + d * sin(self.angle)]
            Mine(center=v, groups=self.groups())
        self.angle += self.delta

    def bump(self, damage=0):
        self.angle += radians(73.0)
        if self.angle >= 4*pi:
            self.angle -= 4*pi
        self.take_damage(damage)


class Spawner(SpriteActor):
    def __init__(self, target_groups=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = 0.0
        self.angle = 0
        self.velocity = 0
        self.hitpoints = 1
        self.physical = False
        self.robots = []
        self.target_groups = target_groups
        self.robots = (BasicRobot, MinedropperRobot)

    def update(self):
        if self.time == 0.0:
            self.time = time.time() + 0.5 # wait 1/2 second on start
        elif time.time() >= self.time: # every five seconds
            self.time = time.time() + 5.0
            angle = random.random() * 2 * pi;
            velocity = random.random() * 1.0 + 1
            newRobot = random.choice(self.robots)
            newRobot(groups=self.target_groups, center=self.rect.center, angle=angle, velocity=velocity)

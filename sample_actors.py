import time
import math

from pygame.rect import Rect
import pygame

from actor import Actor, SpriteActor


class VectorActor(SpriteActor):
    def __init__(self, angle_deg=0, velocity=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = math.radians(angle_deg)
        self.image_angle = self.angle
        self.orig_image_angle = self.angle
        self.velocity = velocity

    def update(self):
        (a, m) = self.angle, self.velocity
        (dx, dy) = (m * math.cos(a), m * math.sin(a))
        self.rect = self.rect.move(dx, -dy)
        if self.image_angle != self.angle:
            self.rotate()

    def bump(self):
        pass

    def rotate(self):
        """rotate image while keeping its center"""
        rot_deg = math.degrees(self.angle - self.orig_image_angle)
        self.image = pygame.transform.rotate(self.orig_image, rot_deg)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.image_angle = self.angle


class BasicRobot(VectorActor):
    """A dumb robot that goes in circles

    Can take damage of bump() until hitpoints is down to zero.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(velocity=50, angle=90, *args, **kwargs)
        self.hitpoints = 0
        self.old_rect = self.rect  # enable step-back on bumping an object

    def take_damage(self, damage):
        self.hitpoints -= damage
        if self.hitpoints <= 0:
            Explosion(center=self.rect.center, angle=self.angle)
            self.die()

    def bump(self, damage=0):
        self.rect = self.old_rect
        self.angle += 73.0
        if self.angle >= 360:
            self.angle -= 360
        if damage: self.take_damage(damage)

    def update(self):
        self.old_rect = self.rect
        self.angle += 1
        if self.angle >= 360:
            self.angle -= 360
        super().update()


class Explosion(SpriteActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = 0.0
        self.physical = False
        self.rect = Rect(self.rect.center)

    def update(self):
        self.time = self.time or time.time()   #init if zero
        if time.time() >= self.time + 3.0:
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
    def __init__(self, shooter, center, angle):
        super().__init__()
        self.shooter = shooter
        self.angle = angle
        self.damage = 1
        self.hitpoints = 1
        self.velocity = 150
        self.rect.center = center

    def bump(self, damage=0):  # hit a mine or a wall
        self.die()


class Wall(SpriteActor):
    def __init__(self, angle=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        angle = angle


class VWall(Wall):
    def __init__(self):
        # img comes from class-name
        super().__init__()


class HWall(Wall):
    def __init__(self):
        # img comes from class-name
        super().__init__()


class MinedropperRobot(SpriteActor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = 135
        self.velocity = 1
        self.hitpoints = 20
        self.delta = 0.0
        self.deltaDirection = "up"
        self.nextMine = 0.0

    def update(self):
        super().update()
        if self.deltaDirection == "up":
            self.delta += 2
            if self.delta > 15.0:
                self.delta = 15.0
                self.deltaDirection = "down"
        else:
            self.delta -= 2
            if self.delta < -15.0:
                self.delta = -15.0
                self.deltaDirection = "up"
        if self.nextMine <= time.time():
            self.nextMine = time.time() + 1.0
            mineX, mineY = self.rect.center

            mineDistance = (self.rect.width / 2.0) ** 2
            mineDistance += (self.rect.height / 2.0) ** 2
            mineDistance = math.sqrt(mineDistance)

            vectorX, vectorY = (math.sin(math.radians(self.angle + self.delta)),
                                math.cos(math.radians(self.angle + self.delta)))
            vectorX, vectorY = vectorX * mineDistance, vectorY * mineDistance
            x, y = self.rect.center
            x -= vectorX
            y += vectorY
            Mine(pos=(x, y))
        self.angle += self.delta

    def bump(self, damage=0):
        self.angle += 73.0
        if self.angle >= 360:
            self.angle -= 360
        self.take_damage(damage)

    def take_damage(self, damage):
        self.hitpoints -= damage
        if self.hitpoints <= 0:
            Explosion(center=self.rect.center, angle=self.angle)
            self.die()



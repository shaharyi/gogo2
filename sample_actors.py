import time
import math

from actor import Actor, SpriteActor
from pygame.rect import Rect


class VectorActor(SpriteActor):
    def __init__(self, angle=90, velocity=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.angle = angle
        self.velocity = velocity

    def update(self):
        (angle, z) = self.angle, self.velocity
        (dx, dy) = (z * math.cos(angle), z * math.sin(angle))
        self.rect = self.rect.move(dx, dy)


class BasicRobot(VectorActor):
    """A dumb robot that goes in circles

    Can take damage of bump() until hitpoints is down to zero.
    """
    MAX_VELOCITY = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


class Score(Actor):
    def __init__(self):
        super().__init__()
        self.value=0
        self.renderer_name='ScoreRenderer'


class Mine(SpriteActor):
    def __init__(self, pos, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hitpoints = 1
        self.rect = pos

    def bump(self):  # dropped over a wall
        self.die()


class Bullet(VectorActor):
    def __init__(self, center):
        super().__init__()
        self.damage = 1
        self.hitpoints = 1
        self.velocity = 150
        self.rect = Rect(self.rect.center)

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

            VectorX, VectorY = (math.sin(math.radians(self.angle + self.delta)),
                                math.cos(math.radians(self.angle + self.delta)))
            VectorX, VectorY = VectorX * mineDistance, VectorY * mineDistance
            x, y = self.rect.center
            x -= VectorX
            y += VectorY
            Mine(center=(x, y))
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



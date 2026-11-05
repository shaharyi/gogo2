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
        (a, m, (x, y)) = self.angle, self.velocity, self.pos
        (dx, dy) = (m * cos(a), m * sin(a))
        x1, y1 = x + dx, y + dy
        self.pos = (x1, y1)
        self.rect = self.rect.move(round(x1 - x), round(y - y1))
        self.rotate()
        super().update()

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
        if damage:
            self.append_sound('bounce')

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
    def __init__(self, velocity=BASE_SPEED/2, image_angle_deg=ORIG_ANGLE, *args, **kwargs):
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
    """A fireball that spins, swells and fades away, centered on the given center."""
    DURATION = 0.6  # seconds
    START_SCALE, END_SCALE = 0.6, 2.4
    SPIN = 0.35  # radians per frame

    def __init__(self, center=None, *args, **kwargs):
        super().__init__(center=center, *args, **kwargs)
        if center:
            self.rect.center = center  # SpriteActor puts the sprite's corner, not its middle, at center
            self.pos = self.rect.topleft
        self.time = time.time()
        self.alpha = 255
        self.render_props.append('alpha')  # clients fade and resize the image to match the rect
        self.physical = False
        self.append_sound('boom')

    def update(self):
        t = (time.time() - self.time) / self.DURATION
        if t >= 1:
            self.die()
            return
        self.angle += self.SPIN
        super().update()  # rotates the image
        swell = 1 - (1 - t) ** 2  # fast at first, then slowing down
        size = round(self.orig_image.get_width() * (self.START_SCALE + (self.END_SCALE - self.START_SCALE) * swell))
        center = self.rect.center
        self.alpha = round(255 * (1 - t) ** 1.5)
        self.image = pygame.transform.scale(self.image, (size, size))
        self.image.set_alpha(self.alpha)
        self.rect = self.image.get_rect(center=center)


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


class HealthBar(SpriteActor):
    """Bar showing the hitpoints of a player, shrinking and turning red as they drop."""
    def __init__(self, player, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = self.image.copy()  # image is cached and shared; draw on our own copy
        self.player = player
        self.max_hitpoints = player.hitpoints
        self.showing = None

    def update(self):
        hp = max(self.player.hitpoints, 0)
        if hp != self.showing:
            self.showing = hp
            w, h = self.image.get_size()
            ratio = hp / self.max_hitpoints
            self.image.fill((60, 60, 60))
            color = (int(255 * (1 - ratio)), int(200 * ratio), 0)
            pygame.draw.rect(self.image, color, (0, 0, round(w * ratio), h))


class Mine(SpriteActor):
    def __init__(self, who=None, ttl=MINE_TTL, *args, **kwargs):
        super().__init__(ttl=ttl, *args, **kwargs)
        self.who = who
        self.hitpoints = 1
        self.ttl_callback = self.blast

    def bump(self):  # dropped over a wall
        self.die()

    def blast(self):
        for i in range(DEBRIS_COUNT):
            d = Debris(self.who, self.rect.center, groups=self.groups())
            i == 0 and d.append_sound('boom')
        self.die()


class Bullet(VectorActor):
    def __init__(self, shooter, center, angle, *args, **kwargs):
        super().__init__(velocity=BASE_SPEED, center=center, angle=angle, *args, **kwargs)
        self.shooter = shooter
        self.damage = 1
        self.hitpoints = 1

    def bounce(self, wall):
        if isinstance(wall, VWall):
            self.angle = pi - self.angle
            self.append_sound('hit')
        elif isinstance(wall, HWall):
            self.angle = -self.angle
            self.append_sound('hit')

    def bump(self, damage=0):  # hit a mine or a wall
        self.die()


DEBRIS_COUNT = 40  # pieces thrown by an exploding mine


class Debris(Bullet):
    """A tiny glowing fragment of an explosion.
    Flies off in a random direction at about bullet speed, cools from yellow to dark red as it
    burns out, and hurts like a bullet (it is one, as far as collisions go).
    """
    PALETTE = [(252, 228, 104), (232, 196, 80), (212, 168, 60), (196, 140, 44), (176, 112, 28), (160, 84, 16)]
    EMBER = (80, 16, 0)  # the color it has cooled to when it burns out
    MIN_SIZE, MAX_SIZE = 3, 8  # pixels; a bullet is 10

    def __init__(self, shooter, center, groups=()):
        ttl = MINE_BLAST_TTL * random.uniform(0.6, 1.4)
        super().__init__(shooter, center, angle=random.uniform(0, 2 * pi), ttl=ttl, groups=groups,
                         image_file='Bullet')  # the file is only a placeholder; the image is drawn below
        self.velocity = BASE_SPEED * random.uniform(0.7, 1.3)
        size = random.randint(self.MIN_SIZE, self.MAX_SIZE)
        self.start_color = self.color = random.choice(self.PALETTE)
        self.image = self.orig_image = pygame.Surface((size, size))
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=center)
        self.pos = self.rect.topleft
        self.render_props.append('color')  # clients draw a square of this color in the size of the rect

    def rotate(self):
        pass  # a square needs no rotating

    def update(self):
        super().update()
        t = min((time.time() - self.start_time) / self.ttl, 1)
        self.color = util.lerp_color(self.start_color, self.EMBER, t)
        self.image.fill(self.color)


class Wall(SpriteActor):
    def __init__(self, topleft, groups, angle=0, *args, **kwargs):
        super().__init__(topleft=topleft, groups=groups, *args, **kwargs)
        angle = angle


class VWall(Wall):
    pass


class HWall(Wall):
    pass


CAMP_H = 152  # height of a camp: two 16px HWalls around four 32px VWalls, plus 8px of overhang
CAMP_Y = (HEIGHT - CAMP_H) // 2  # camps are centered vertically on the screen
LEFT_CAMP_X = 68  # left edge of the left camp; it opens towards the left edge of the screen
# the right camp is the mirror image of the left one around the screen's vertical center line
RIGHT_CAMP_X = WIDTH - LEFT_CAMP_X - 48
# the player starts inside the right camp, centered between its HWalls
PLAYER_START = (RIGHT_CAMP_X + 16, CAMP_Y + CAMP_H // 2 - 16)


def create_walls(static_group):
    g = (static_group, )
    for x, hwall_x in ((LEFT_CAMP_X + 32, LEFT_CAMP_X), (RIGHT_CAMP_X, RIGHT_CAMP_X + 16)):
        for i in range(4):
            VWall((x, CAMP_Y + 8 + 32 * i), g)
        HWall((hwall_x, CAMP_Y), g)
        HWall((hwall_x, CAMP_Y + CAMP_H - 16), g)


class MinedropperRobot(Robot):
    def __init__(self, velocity=BASE_SPEED/5, image_angle_deg=ORIG_ANGLE, *args, **kwargs):
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
            Mine(who=self, center=v, groups=self.groups())
        self.angle += self.delta

    def killed_actor(self, _actor):
        pass

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
            velocity = random.random() * BASE_SPEED + 1
            newRobot = random.choice(self.robots)
            newRobot(groups=self.target_groups, center=self.rect.center, angle=angle, velocity=velocity)

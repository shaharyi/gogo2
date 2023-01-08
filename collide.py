from multimethod import multimethod

from sample_actors import *
from player_actor import PlayerActor


def check_boundaries(_actor, rect):
    x, y = map(round, _actor.rect.topleft)
    w, h = _actor.rect.size
    left, right = (x < 0), (x + w > rect.w)
    top, bottom = (y < 0), (y + h > rect.h)
    return left, right, top, bottom


def handle_collisions(rect, groups):
    coll_group = pygame.sprite.Group()
    sprites = [s for sg in groups for s in sg.sprites()]
    for s in sprites:
        where = check_boundaries(s, rect)
        if any(where):  # with world boundaries
            s.bump()
        collisions = pygame.sprite.spritecollide(s, coll_group, dokill=False)
        coll_group.add(s)
        for c in collisions:
            collide(s, c)


@multimethod
def collide(_a1: SpriteActor, _a2: SpriteActor):
    # Default collision - do nothing
    return 1


@multimethod
def collide(_actor: SpriteActor, _wall: Wall):
    _actor.bump()
    return 1


@multimethod
def collide(_wall: Wall, _actor: SpriteActor):
    return 1


def center_inside(_a1: SpriteActor, _a2: SpriteActor):
    return _a2.rect.collidepoint(_a1.rect.center)


def most_collide(_a1: SpriteActor, _a2: SpriteActor):
    return center_inside(_a1, _a2) or center_inside(_a2, _a1)


@multimethod
def collide(_bullet: Bullet, _wall: Wall):
    if most_collide(_bullet, _wall):
        _bullet.bump()
    else:
        _bullet.bounce(_wall)
    return 1


@multimethod
def collide(_wall: Wall, _bullet: Bullet):
    return collide(_bullet, _wall)


@multimethod
def collide(_actor: BasicRobot, _mine: Mine):
    _actor.bump(damage=25)
    _mine.die()
    return 1


@multimethod
def collide(_mine: Mine, _actor:BasicRobot):
    return collide(_actor, _mine)


@multimethod
def collide(_actor: PlayerActor, _mine: Mine):
    _actor.bump(damage=5)
    _mine.die()
    return 1


@multimethod
def collide(_mine: Mine, _actor:PlayerActor):
    return collide(_actor, _mine)


@multimethod
def collide(_bullet: Bullet, _actor: Robot):
    _actor.bump(damage=_bullet.damage)
    if _actor.hitpoints == 0 and _bullet.shooter:
        _bullet.shooter.killed_actor(_actor)
    _bullet.die()
    return 1


@multimethod
def collide(_actor: Robot, _bullet: Bullet):
    return collide(_bullet, _actor)


@multimethod
def collide(actor1: Robot, actor2: Robot):
    actor1.bump(damage=25)
    actor2.bump(damage=25)


@multimethod
def collide_mines(mine1: Mine, mine2: Mine):
    mine1.die()
    mine2.die()
    Explosion(center=mine1.rect.center)


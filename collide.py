from multimethod import multimethod

from sample_actors import *
from world import World


@multimethod
def collide(_a1: Actor, _a2: Actor):
    # Default collision - do nothing
    return 1


@multimethod
def collide(_actor: Actor, _wall: Wall):
    _actor.bump()
    return 1


@multimethod
def collide(_wall: Wall, _actor: Actor):
    return collide(_actor, _wall)


@multimethod
def collide(_actor:Robot, _mine: Mine):
    _actor.bump(damage=25)
    _mine.die()
    return 1


@multimethod
def collide(_mine: Mine, _actor:Robot):
    return collide(_actor, _mine)


@multimethod
def collide(_bullet: Bullet, _actor: Robot):
    _actor.bump(damage=_bullet.damage)
    if _actor.hitpoints == 0:
        _bullet.shooter.killed_actor(_actor)
    _bullet.die()
    return 1


@multimethod
def collide(_actor: Robot, _bullet: Bullet):
    return collide(_bullet, _actor)


@multimethod
def collide(_mine: Mine, _world: World, where):
    # if a mine is laid outside the world boundaries - erase it
    _mine.die()


@multimethod
def collide(_actor: VectorActor, _world: World, where):
    _actor.bump()


@multimethod
def collide(actor1: Robot, actor2: Robot):
    actor1.bump(damage=25)
    actor2.bump(damage=25)


@multimethod
def collide_mines(mine1: Mine, mine2: Mine):
    mine1.die()
    mine2.die()
    Explosion(center=mine1.rect.center)


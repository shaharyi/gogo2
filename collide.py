from multimethod import multimethod

from sample_actors import *
from world import World

@multimethod
def collide_actor_wall(_actor: Actor, _wall: Wall):
    _actor.bump()
    return 1


@multimethod
def collide_actor_actor(_a1:Actor, _a2: Actor):
    "Default collision - do nothing"
    return 1


@multimethod
def collide_actor_mine(_actor: Actor, _mine: Mine):
    _actor.bump(damage=25)
    _mine.die()
    return 1


@multimethod
def collide_bullet_actor(_bullet: Bullet, _actor: Actor):
    _actor.bump(damage=_bullet.damage)
    if _actor.hitpoints == 0:
        _bullet.shooter.killed_actor(_actor)
    _bullet.die()
    return 1


@multimethod
def collide_bullet_world(_bullet: Bullet, _world: World, where):
    _bullet.die()
    return 1


@multimethod
def collide_mine_world(_mine: Mine, _world: World, where):
    "If a mine is layed outside the world boundaries - erase it"
    _mine.die()


@multimethod
def collide_actor_world(_actor: Actor, _world: World, where):
    _actor.bump()

@multimethod
def collide_actor_world(_actor: Actor, _world: World, where):
    _actor.bump()


@multimethod
def collide_mobile_actors(actor1: Actor, actor2: Actor):
    actor1.bump(damage=25)
    actor2.bump(damage=25)


@multimethod
def collide_mines(mine1: Mine, mine2: Mine):
    mine1.die()
    mine2.die()
    Explosion(center=mine1.rect.center)


def rev_args(_method):
    return lambda x, y: _method(y, x)


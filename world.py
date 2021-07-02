import math, time, sys

from greenlet import greenlet
import pygame, pygame.locals

from util import log
from actor import Actor
import collide


class WorldState:
    """A snapshot of the world sent to all actors, both local and remote"""

    def __init__(self, updateRate, time):
        self.updateRate = updateRate
        self.time = time
        self.actors = []


class World(Actor):
    """The playground that runs the business.

    Respon:
    Make all actors tick()
    Make sure every frame (tick) takes the same time to do.
    Scan actors collisions amongst themeselves and with the World boundaries.

    Collab:
    All actors JOIN World.
    Sends actors snapshots of the world.
    Forward INPUT msgs to player (usually gotten from server).
    """
    singleton = None

    def __init__(self):
        World.singleton = self
        Actor.__init__(self)
        print("world id=", self.id)
        self.registeredActors = {}
        self.updateRate = 30
        self.maxupdateRate = 30
        self.checkpoint = 0
        self.height = 496
        self.width = 496
        greenlet(self.runFrame)

    def kill_dead_actors(self):
        for id in self.registeredActors.keys():
            _actor = self.registeredActors[id]
            if hasattr(_actor, 'hitpoints'):
                if _actor.hitpoints <= 0:
                    print("ACTOR", id, "DIED, hitpoints=", self.registeredActors[id].hitpoints)
                    _actor.channel.send_exception(TaskletExit)
                    del self.registeredActors[id]

    def test_collision_with_actor(self, _actor):
        x, y = map(round, _actor.rect.topleft)
        w, h = _actor.rect.size
        left, right = (x < 0), (x + w > self.width)
        top, bottom = (y < 0), (y + h > self.height)
        return left, right, top, bottom

    def scanActorImpacts(self):
        SpriteActor.sprite_group.update()
        coll_group = pygame.sprite.Group()
        for id in self.registeredActors.keys():
            _actor = self.registeredActors[id]
            if _actor.public and _actor.physical:
                where = self.test_collision_with_actor(_actor)
                if True in where:  # with world boundaries
                    self.collide(_actor, self, where)
                # return sprite-list, don't kill (=coll_group.remove) colliding
                collisions = pygame.sprite.spritecollide(_actor, coll_group, False)
                coll_group.add(_actor)
                for c in collisions:
                    print(' ** collision',
                          c.__class__.__name__,
                          c.rect,
                          _actor.__class__.__name__,
                          _actor.rect)
                    self.collide(_actor, c)

    def sendStateToActors(self, starttime):
        worldState = WorldState(self.updateRate, starttime)
        for id, _actor in self.registeredActors.items():
            if _actor.public:
                # print 'adding', id, self.registeredActors[id]
                worldState.actors.append((id, myvars(_actor)))
        for id, _actor in self.registeredActors.items():
            if not _actor.public:  # only to Server and Display
                # print "sending state to %s" % _actor.name
                _actor.channel.send((self.id, "WORLD_STATE", worldState, self.checkpoint))
        self.checkpoint = 0

    def actorsTick(self):
        for id, _actor in self.registeredActors.items():
            _actor.tick(self.updateRate)

    def runFrame(self):
        initialStartTime = time.time()
        startTime = time.time()
        while 1:
            self.kill_dead_actors()
            self.actorsTick()
            self.scanActorImpacts()
            self.sendStateToActors(startTime)
            # wait
            calculatedEndTime = startTime + 1.0 / self.updateRate
            doneProcessingTime = time.time()
            percentUtilized = (doneProcessingTime - startTime) / (1.0 / self.updateRate)
            if percentUtilized >= 1:
                self.updateRate -= 1
                print("TOO MUCH PROCESSING, LOWERING FRAME RATE: ", self.updateRate)
            elif percentUtilized <= 0.6 and self.updateRate < self.maxupdateRate:
                self.updateRate += 1
                print("TOO MUCH FREETIME, RAISING FRAME RATE: ", self.updateRate)
            while time.time() < calculatedEndTime:
                self.greenlet.parent.switch()
            startTime = calculatedEndTime
            self.greenlet.parent.switch()

    def defaultMessageAction(self, args):
        sentFrom, msg, msgArgs = args[0], args[1], args[2:]
        if msg == "INPUT":
            # usually gotten from server, so fwd to player
            self.checkpoint = time.time()
            # print "World INPUT", time.time()-self.checkpoint, self.registeredActors.items()[1][1].angle
            # if self.registeredActors.has_key(sentFrom):
            Actor.actors[sentFrom].channel.send((self.id, "INPUT") + msgArgs)
        elif msg == "JOIN":
            # props= msgArgs[0] #myvar dict instance
            # print "joined:", sentFrom, props['name'], str(props)
            self.registeredActors[sentFrom] = Actor.actors[sentFrom]
        elif msg == "COLLISION":
            pass  # known, but we don't do anything
        elif msg == "KILLME":
            self.registeredActors[sentFrom].hitpoints = 0
        else:
            print
            '!!!! WORLD GOT UNKNOWN MESSAGE ', msg, msgArgs


from sample_actors import BasicRobot
# from world import World


class PlayerActor(BasicRobot):
    """Player sprite

    Respon:
    Follows the physical model of a amusement colliding cars, with friction and
    thrust (-5, 0 or 5).
    It counts active players (nplayers) to load the right sprite image.

    Collab:
    Receive INPUT msgs (originated at Client Display, forwarded by Server) and change velocity/angle accordingly.
    """
    veloc_d = 0
    angle_d = 0
    THRUST  = 5
    FRICTION= 3
    last_input_time = 0
    #incremental value to add to current angle
    angle_cmd  = { pygame.K_RIGHT: .5, pygame.K_LEFT: -.5 }
    #exact value to use as thrust
    thrust_cmd = { pygame.K_UP: THRUST, pygame.K_DOWN: -THRUST }
    nplayers = 0

    def __init__(self, location):
        # location = location or (PlayerActor.nplayers%2 and 50  or World._singleton.width-50, 250)
        super.__init__(location=location)
        self.angle = 90
        self.velocity = 0
        self.hitpoints = 20
        self.thrust = 0
        PlayerActor.nplayers += 1
        self.image_file = self.__class__.__name__ + str(PlayerActor.nplayers) + IMAGE_EXT
        score_loc = PlayerActor.nplayers==1 and (0,0) or (World._singleton.width-50, 0)
        self.score = Score(world=self.world, player=self, location=score_loc, physical=False)

    def die(self):
        PlayerActor.nplayers -=1
        BasicRobot.die(self)
        self.score.die()

    def drop_mine(self):
        mineDistance =  self.rect.h
        v = [math.cos(math.radians(self.angle+90)),
             math.sin(math.radians(self.angle+90))]
        loc= [0,0]
        for d in (0,1):
            v[d] *= mineDistance
            loc[d] = self.location[d] + self.rect[d+2]/2 + v[d]
        Mine(center=tuple(loc), world=self.world)

    def shoot(self):
        distance =  self.rect.h
        v = [math.cos(math.radians(self.angle+90)),
             math.sin(math.radians(self.angle+90))]
        loc= [0,0]
        for d in (0,1):
            v[d] *= distance
            loc[d] = self.location[d] + self.rect[d+2]/2 - v[d]
        Bullet(shooter=self, center=tuple(loc), angle=self.angle, world=self.world)

    def killed_actor(self, _target):
        "Called when we kill another player or robot"
        self.score.value += _target.__class__.__name__=='PlayerActor' and 100 or 10

    def handle_INPUT(self, msg):
        sentFrom, msg, msgArgs = msg[0],msg[1],msg[2:]
        #print "PlayerActor:", time.time() - self.last_input_time
        event_type, keycode = msgArgs[0:2]
        a_d = self.angle_cmd.get(keycode,0) * 10.0
        if event_type == pygame.KEYDOWN:
            self.last_input_time = msgArgs[2]
            self.thrust = self.thrust_cmd.get(keycode, self.thrust)
            if a_d: self.angle_d =  a_d
        else: #KeyUp
            if keycode in self.thrust_cmd.keys(): self.thrust = 0
            if a_d: self.angle_d = 0
        if keycode == pygame.K_m and event_type == pygame.KEYDOWN:
            self.drop_mine()
        if keycode == pygame.K_SPACE and event_type == pygame.KEYDOWN:
            self.shoot()

    def bump(self, damage=0):
        #may be not enough if updateRate increased since last tick
        MobileActor.step_back(self)
        self.velocity = 0
        if damage: self.take_damage(damage)

    def tick(self, updateRate):
        d_v = self.thrust - sign(self.velocity)*self.FRICTION
        self.velocity += abs(self.velocity+d_v)<=self.MAX_VELOCITY  and  d_v or 0
        self.angle    += self.angle_d
        self.angle  = self.angle<0 and self.angle%-360 or self.angle%360
        MobileActor.tick(self,updateRate)

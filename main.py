import random
import pygame
from pygame.locals import *

from player_actor import PlayerActor
from sample_actors import *
from collide import collide


def check_boundaries(_actor, screen):
    area = screen.get_rect()
    x, y = map(round, _actor.rect.topleft)
    w, h = _actor.rect.size
    left, right = (x < 0), (x + w > area.width)
    top, bottom = (y < 0), (y + h > area.height)
    return left, right, top, bottom


def handle_collisions(screen, groups):
    coll_group = pygame.sprite.Group()
    sprites = [s for sg in groups for s in sg.sprites()]
    for s in sprites:
        where = check_boundaries(s, screen)
        if any(where):  # with world boundaries
            s.bump()
        collisions = pygame.sprite.spritecollide(s, coll_group, dokill=False)
        coll_group.add(s)
        for c in collisions:
            collide(s, c)


def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption('Gogo2')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    background_orig = background.copy()  # in case static sprites change

    # Initialise actors
    rand = ((0.1 * (random.randint(5,8))))
    # ball = Mine((0,0),(0.47,speed))
    score_loc = PlayerActor.nplayers == 1 and (0, 0) or (screen.get_width() - 50, 0)
    score = Score(topleft=score_loc)
    dynamic_group = pygame.sprite.RenderPlain()
    # Initialise sprites
    player1 = PlayerActor(topleft=screen.get_rect().center, score=score, groups=(dynamic_group,))

    static_group = pygame.sprite.RenderPlain()
    create_walls(static_group)
    spawner = Spawner(topleft=(232, 232), target_groups=(dynamic_group,), groups=(static_group,))

    static_group.draw(background)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    # Initialise clock
    clock = pygame.time.Clock()

    # Event loop
    while 1:
        # Make sure game doesn't run at more than 60 frames per second
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE):
                return
            player1.process_input(event)

        for sp in dynamic_group.sprites():
            screen.blit(background, sp.rect, sp.rect)
        spawner.update()
        dynamic_group.update()
        handle_collisions(screen, (static_group, dynamic_group))
        dynamic_group.draw(screen)
        pygame.display.flip()


def create_walls(static_group):
    VWall(topleft=(370, 200), groups=(static_group,))
    VWall(topleft=(370, 232), groups=(static_group,))
    VWall(topleft=(370, 264), groups=(static_group,))
    VWall(topleft=(370, 296), groups=(static_group,))
    HWall(topleft=(378, 200), groups=(static_group,))
    HWall(topleft=(378, 320), groups=(static_group,))

    VWall(topleft=(100, 200), groups=(static_group,))
    VWall(topleft=(100, 232), groups=(static_group,))
    VWall(topleft=(100, 264), groups=(static_group,))
    VWall(topleft=(100, 296), groups=(static_group,))
    HWall(topleft=(76, 192), groups=(static_group,))
    HWall(topleft=(76, 328), groups=(static_group,))


if __name__ == '__main__':
    main()


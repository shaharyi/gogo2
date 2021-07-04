import random
import pygame
from pygame.locals import *

from player_actor import PlayerActor
from sample_actors import *


def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption('Gogo2')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    # Initialise actors
    rand = ((0.1 * (random.randint(5,8))))
    # ball = Mine((0,0),(0.47,speed))
    score_loc = PlayerActor.nplayers == 1 and (0, 0) or (screen.get_width() - 50, 0)
    score = Score(topleft=score_loc)
    player1 = PlayerActor(topleft=screen.get_rect().center, score=score)
    # Initialise sprites
    playersprites = pygame.sprite.RenderPlain((player1, ))

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

        screen.blit(background, player1.rect, player1.rect)
        playersprites.update()
        playersprites.draw(screen)
        pygame.display.flip()


if __name__ == '__main__':
    main()


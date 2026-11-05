from pdb import set_trace
import pygame
from pygame.locals import QUIT

from player_actor import PlayerActor
from sample_actors import Spawner, create_walls, PLAYER_START
from collide import handle_collisions
from config import *
import util


def main():
    # Initialise screen
    if pygame.get_sdl_version()[0] == 2:
        pygame.mixer.pre_init(44100, 32, 2, 1024)
    pygame.init()
    sound_bank = {name: util.load_sound(name + '.wav') for name in 'shoot boom bounce hit'.split()}
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED if SCALED else 0)
    pygame.display.set_caption('Gogo2')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    background_orig = background.copy()  # in case static sprites change

    dynamic_group = pygame.sprite.RenderPlain()
    # Initialise sprites
    player1 = PlayerActor(topleft=PLAYER_START, groups=(dynamic_group,))

    static_group = pygame.sprite.RenderPlain()
    create_walls(static_group)
    spawner = Spawner(topleft=(0, 0), target_groups=(dynamic_group,), groups=(static_group,))
    spawner.rect.center = screen.get_rect().center  # middle of the screen

    static_group.draw(background)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    # Initialise clock
    clock = pygame.time.Clock()

    # Event loop
    while 1:
        # Make sure game doesn't run at more than FPS frames per second
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                player1 = PlayerActor(topleft=PLAYER_START, groups=(dynamic_group,))
            elif event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                player1.process_input((event.type, util.physical_key(event)))

        for sp in dynamic_group.sprites():
            screen.blit(background, sp.rect, sp.rect)
        spawner.update()
        dynamic_group.update()
        handle_collisions(screen.get_rect(), (static_group, dynamic_group))
        for sp in static_group.sprites() + dynamic_group.sprites():
            for name in sp.sounds:
                sound = sound_bank.get(name)
                sound and sound.play()
        dynamic_group.draw(screen)
        pygame.display.flip()


if __name__ == '__main__':
    main()


from pdb import set_trace
import sys
from asyncio.protocols import DatagramProtocol
import asyncio

from pygame.locals import QUIT
import pygame
from pygame import Surface
import pickle

import util
from config import *

images = {}   # filepath -> Surface
surfaces = []


def process_render_data(data):
    surf_list = []
    for render_props in data:
        props = dict(render_props)
        fp = props['filepath']
        angle = props.get('angle')
        rect = props['rect']
        img = images.get(fp)
        img = img or pygame.image.load(props['filepath']).convert()
        if angle and angle != ORIG_ANGLE:
            img = util.rotate(img, angle - ORIG_ANGLE)
        surf_list.append((img, rect.topleft))
    return surf_list


def process_udp_msg(msg):
    op, pay = msg
    global surfaces
    surfaces = []
    if op == 'WORLD_STATE':
        surfaces = process_render_data(pay)
    else:
        util.log('Unknown msg: %s' % op)


# UDP  client
class UDPClientProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print("Received:", data.decode())
        msg = pickle.loads(data)
        process_udp_msg(msg)

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")


async def main():
    print('TCP connect')
    host = len(sys.argv) > 1 and sys.argv[1] or '127.0.0.1'
    reader, writer = await asyncio.open_connection(host, TCP_PORT)
    message = ('NEW_PLAYER', None)  # no args
    msg = util.prepare_msg(message)
    print(f'Send: {msg!r}')
    writer.write(msg)
    # if reached high watermark, drain down to lower watermark
    await writer.drain()

    nbytes, msg = await util.read_tcp_msg(reader)
    opcode, payload = msg
    static_sprites = []
    if opcode == 'STATIC_SPRITES':
        static_sprites = payload
    else:
        util.log('Unknown msg: ' + opcode)

    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    ip = MCAST and MCAST_GROUP or '127.0.0.1'
    udp_transport, udp_protocol = await loop.create_datagram_endpoint(
        UDPClientProtocol,
        remote_addr=(ip, UDP_PORT))

    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Gogo2')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    background_orig = background.copy()  # in case static sprites change

    surf_list = process_render_data(static_sprites)
    for surf, pos in surf_list:
        background.blit(surf, pos)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    # Initialise clock
    clock = pygame.time.Clock()

    done = False
    # Event loop
    while not done and not udp_transport.is_closing():
        # Make sure game doesn't run at more than 60 frames per second
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE):
                done = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                msg = util.prepare_msg(('NEW_PLAYER', None))
                writer.write(msg)
            elif event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                msg = util.prepare_msg(('INPUT', event.type, event.key))
                writer.write(msg)
        if not done:
            for surf, pos in surfaces:
                background.blit(surf, pos)
            pygame.display.flip()

    print('Close UDP connection')
    udp_transport.close()

    print('Close TCP connection...')
    writer.close()
    await writer.wait_closed()
    print('TCP connection closed')


asyncio.run(main())
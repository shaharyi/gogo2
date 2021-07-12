from pdb import set_trace
from math import degrees, pi
import sys
import socket
import struct
from asyncio.protocols import DatagramProtocol
import asyncio

from pygame.locals import QUIT
import pygame
import pickle

import util
from config import *

images = {}   # filepath -> Surface
surfaces = []

ORIG_ANGLE_RAD = ORIG_ANGLE * pi/180


def process_render_data(data):
    surf_list = []
    for render_props in data:
        props = dict(render_props)
        fp = props['filepath']
        angle = props.get('angle')
        rect = props['rect']
        img = images.get(fp)
        img = img or pygame.image.load(props['filepath']).convert()
        diff = angle and angle - ORIG_ANGLE_RAD
        if diff:
            img = util.rotate(img, degrees(diff))
        surf_list.append((img, rect.topleft))
    return surf_list


def process_udp_msg(msg):
    op, prop_surfaces, raw_surfaces = msg[0], msg[1], msg[2]
    global surfaces
    surfaces = []
    if op == 'RENDER_DATA':
        surfaces = process_render_data(prop_surfaces)
        more = [(pygame.image.frombuffer(s[0], s[1][2:4], 'RGBA'), s[1][0:2]) for s in raw_surfaces]
        surfaces += more
    else:
        util.log('Unknown msg: %s' % op)


# UDP  client
class UDPClientProtocol(DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        print("UDP Connected")
        self.transport = transport
        # message = 'hello'
        # print('Send:', message)
        # self.transport.sendto(message.encode())

    def datagram_received(self, data, addr):
        # print("Received %d", len(data))
        msg = pickle.loads(data)
        process_udp_msg(msg)

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")


async def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Gogo2')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    background_orig = background.copy()  # in case static sprites change

    server_ip = len(sys.argv) > 1 and sys.argv[1] or LOCAL_IP
    print('Connect to ' + server_ip)

    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    remote_ip = MCAST and MCAST_GROUP or UCAST and server_ip
    remote_addr = UCAST and (remote_ip, UDP_PORT) or None
    local_addr = BCAST and (BCAST_IP, UDP_PORT) or MCAST and ('', UDP_PORT) or None
    print(f'local={local_addr}, remote={remote_addr}')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ## s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if BCAST:
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if local_addr:
        sock.bind(local_addr)
    if MCAST:
        # Tell the operating system to add the socket to
        # the multicast group on all interfaces.
        group = socket.inet_aton(MCAST_GROUP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    if remote_addr:
        sock.connect(remote_addr)

    udp_transport, udp_protocol = await loop.create_datagram_endpoint(
        UDPClientProtocol, sock=sock)
        # local_addr=local_addr,
        # remote_addr=remote_addr)
    udp_local_addr = udp_transport.get_extra_info('sockname')
    print(f'udp_local_addr ={udp_local_addr}')
    # peername = udp_transport.get_extra_info('peername')
    # print(f'peername = {peername}')

    print('TCP connect to ' + str(server_ip))
    reader, writer = await asyncio.open_connection(server_ip, TCP_PORT)
    tcp_local_addr = writer.get_extra_info('sockname')
    peer = writer.get_extra_info('peername')
    message = ('NEW_PLAYER', udp_local_addr)
    msg = util.prepare_msg(message)
    print(f'Send: {message!r} to {peer}')
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
        # receive UDP packets
        await asyncio.sleep(0.01)
        # Make sure game doesn't run at more than 60 frames per second
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE):
                done = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                msg = util.prepare_msg(('NEW_PLAYER', udp_local_addr))
                writer.write(msg)
            elif event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                msg = util.prepare_msg(('INPUT', event.type, event.key))
                writer.write(msg)
        if not done:
            screen.blit(background, (0, 0))
            for surf, pos in surfaces:
                screen.blit(surf, pos)
            pygame.display.flip()

    print('Close UDP connection')
    udp_transport.close()

    print('Close TCP connection...')
    writer.close()
    await writer.wait_closed()
    print('TCP connection closed')


asyncio.run(main())

from pdb import set_trace
from math import degrees, pi
import sys
import socket
import string
import struct
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
    op, pay = msg
    global surfaces
    surfaces = []
    if op == 'RENDER_DATA':
        surfaces = process_render_data(pay)
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
        if MCAST:
            s = transport.get_extra_info("socket")
            #
            # Allow multiple copies of this program on one machine
            # (not strictly needed)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #
            # Bind it to the port (default/all interfaces)
            s.bind(('0.0.0.0', UDP_PORT))
            #
            # Look up multicast group address in name server
            # (doesn't hurt if it is already in ddd.ddd.ddd.ddd format)
            group = socket.gethostbyname(MCAST_GROUP)
            #
            # Construct binary group address
            bytes = map(int, group.split("."))
            grpaddr = 0
            for byte in bytes: grpaddr = (grpaddr << 8) | byte
            #
            # Construct struct mreq from grpaddr and ifaddr
            ifaddr = socket.INADDR_ANY
            mreq = struct.pack('ll', socket.htonl(grpaddr), socket.htonl(ifaddr))
            #
            # Add group membership
            s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            #

    def datagram_received(self, data, addr):
        # print("Received %d", len(data))
        msg = pickle.loads(data)
        process_udp_msg(msg)

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")


async def main():
    server_ip = len(sys.argv) > 1 and sys.argv[1] or '127.0.0.1'
    print('Connect to ' + server_ip)

    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ## s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # s.bind(('192.168.1.255', 3001))
    remote_ip = MCAST and MCAST_GROUP or UCAST and server_ip
    remote_addr = (MCAST or UCAST) and (remote_ip, UDP_PORT) or None
    local_addr = BCAST and (BCAST_IP, UDP_PORT) or None
    print(f'local={local_addr}, remote={remote_addr}')
    udp_transport, udp_protocol = await loop.create_datagram_endpoint(
        UDPClientProtocol,  # sock=s)
        local_addr=local_addr,
        remote_addr=remote_addr)
    udp_local_addr = udp_transport.get_extra_info('sockname')
    peer = udp_transport.get_extra_info('peername')

    print('TCP connect to ' + str(peer))
    reader, writer = await asyncio.open_connection(server_ip, TCP_PORT)
    message = ('NEW_PLAYER', udp_local_addr)
    msg = util.prepare_msg(message)
    print(f'Send: {message!r} to {udp_local_addr}')
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

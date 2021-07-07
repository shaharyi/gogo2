from asyncio.protocols import DatagramProtocol
import asyncio
import socket
import os, random
import struct
import pickle

from pygame import Rect

import util
from player_actor import PlayerActor
from actor import serialize_sprites
from collide import *
from config import *


class Server:
    def new_player(self):
        score_loc = (self.screen_rect.h + 50 * PlayerActor.nplayers, 0)
        score = Score(topleft=score_loc)
        # Initialise sprites
        player = PlayerActor(topleft=self.screen_rect.center, score=score, groups=(self.dynamic_group,))
        self.players.append(player)
        return player

    def initialise_actors(self):
        self.create_walls()
        Spawner(center=self.screen_rect.center,
                target_groups=(self.dynamic_group,),
                groups=(self.spawner_group,))

    def __init__(self):
        self.players = []
        self.screen_rect = Rect(0, 0, WIDTH, HEIGHT)
        self.dynamic_group = pygame.sprite.RenderPlain()
        self.static_group = pygame.sprite.RenderPlain()
        self.spawner_group = pygame.sprite.RenderPlain()
        self.initialise_actors()
        self.transport = None

    def create_walls(self):
        g = (self.static_group, )
        VWall((370, 200), g)
        VWall((370, 232), g)
        VWall((370, 264), g)
        VWall((370, 296), g)
        HWall((378, 200), g)
        HWall((378, 320), g)
        VWall((100, 200), g)
        VWall((100, 232), g)
        VWall((100, 264), g)
        VWall((100, 296), g)
        HWall((76, 192), g)
        HWall((76, 328), g)

    def broadcast(self):
        groups = (self.static_group, self.dynamic_group, self.spawner_group)
        data = serialize_sprites(*groups)
        buf = pickle.dumps(data)
        self.transport.sendto(buf, ('192.168.1.255', 9000))

    def process_tcp_msg(self, args, writer, player):
        opcode, payload = args[0], args[1:]
        if opcode in ('JOIN', 'NEW_PLAYER'):
            sprites_data = serialize_sprites(self.static_group)
            msg = util.prepare_msg(('STATIC_SPRITES', sprites_data))
            writer.write(msg)
        if opcode == 'NEW_PLAYER':
            if player is None:
                player = self.new_player()
            else:
                util.log('Bug - a new player joins from same connection')
        elif opcode == 'INPUT':
            player.process_input(payload)
        else:
            print("Unknown msg: " + opcode)
        return player

    async def tcp_socket_handler(self, reader, writer):
        addr = writer.get_extra_info('peername')
        done = False
        player = None
        while not done:
            if writer.is_closing():
                done = True
            r, msg = await util.read_tcp_msg(reader)
            print("server got (%d) from %s: %s " % (r, addr, str(msg)))
            player = self.process_tcp_msg(msg, writer, player)
        writer.close()
        await writer.wait_closed()

    class UDPServerProtocol(DatagramProtocol):
        def __init__(self):
            super().__init__()
            self.transport = None

        def connection_made(self, transport):
            self.transport = transport
            print('UDP connection made')
            sock = transport.get_extra_info("socket")
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if MCAST:
                ttl = struct.pack('b', 1)  # Time-to-live
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            else:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        def datagram_received(self, data, addr):
            message = data.decode()
            print('UDP datagram received %r from %s' % (message, addr))

    async def main(self):
        print("Starting TCP server")
        tcp_server = await asyncio.start_server(self.tcp_socket_handler, 'localhost', TCP_PORT)

        addr = tcp_server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        print("Starting UDP server")
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()
        # One protocol instance will be created to serve all
        # client requests.
        self.transport, protocol = await loop.create_datagram_endpoint(
            self.UDPServerProtocol,
            local_addr=('localhost', UDP_PORT))

        pygame.font.init()  # for Score

        # Initialise clock
        clock = pygame.time.Clock()
        try:
            while True:
                # Make sure game doesn't run at more than X frames per second
                clock.tick(30)
                self.broadcast()
                # Yield to asyncio event-loop
                await asyncio.sleep(0)
                self.spawner_group.update()
                self.dynamic_group.update()
                handle_collisions(self.screen_rect, (self.static_group, self.dynamic_group))
        finally:
            self.transport.close()
            tcp_server.close()
            await tcp_server.wait_closed()


server = Server()
asyncio.run(server.main())

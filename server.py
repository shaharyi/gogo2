from asyncio.protocols import DatagramProtocol
import asyncio
import socket
import struct
import pickle

from pygame import Rect

from player_actor import PlayerActor
from actor import serialize_sprites
from collide import *
from config import *


class Server:
    def __init__(self):
        self.players = []
        self.udp_peer_addr = {}
        self.screen_rect = Rect(0, 0, WIDTH, HEIGHT)
        self.dynamic_group = pygame.sprite.RenderPlain()
        self.static_group = pygame.sprite.RenderPlain()
        self.spawner_group = pygame.sprite.RenderPlain()
        self.initialise_actors()
        self.transport = None

    def new_player(self, num):
        # Initialise sprites
        player = PlayerActor(topleft=self.screen_rect.center, local=False, groups=(self.dynamic_group,), num=num)
        self.players.append(player)
        return player

    def initialise_actors(self):
        self.create_walls()
        Spawner(topleft=(232, 232),  # center=self.screen_rect.center,
                target_groups=(self.dynamic_group,),
                groups=(self.spawner_group,))

    def create_walls(self):
        g = (self.static_group, )
        VWall((370, 200), g)
        VWall((370, 232), g)
        VWall((370, 264), g)
        VWall((370, 296), g)
        HWall((386, 196), g)
        HWall((386, 316), g)
        VWall((100, 200), g)
        VWall((100, 232), g)
        VWall((100, 264), g)
        VWall((100, 296), g)
        HWall((68, 196), g)
        HWall((68, 316), g)

    def transmit(self, msg):
        buf = pickle.dumps(msg)
        if BCAST:
            self.transport.sendto(buf, (BCAST_IP, UDP_PORT))
        elif MCAST:
            self.transport.sendto(buf, (MCAST_GROUP, UDP_PORT))
            # print('sending %d' % len(buf))
        else:  # unicast
            for addr in self.udp_peer_addr.items():
                # print('sending %d to %s' % (len(buf), addr))
                self.transport.sendto(buf, addr)

    def pack_groups(self):
        groups = (self.dynamic_group, self.spawner_group)
        return serialize_sprites(*groups)

    def pack_surfaces(self):
        surfaces = []
        for p in self.players:
            sprit = p.score
            surfaces.append((pygame.image.tostring(sprit.image, 'RGBA'), sprit.rect))
        return tuple(surfaces)

    def pack_and_transmit(self):
        gr = self.pack_groups()
        sf = self.pack_surfaces()
        msg = ('RENDER_DATA', gr, sf)
        self.transmit(msg)

    def process_tcp_msg(self, args, writer, player, num):
        opcode, payload = args[0], args[1:]
        if opcode in ('JOIN', 'NEW_PLAYER'):
            ip, port = payload[0]
            if UCAST:
                self.udp_peer_addr[ip] = port
            sprites_data = serialize_sprites(self.static_group)
            msg = util.prepare_msg(('STATIC_SPRITES', sprites_data))
            writer.write(msg)
        if opcode == 'NEW_PLAYER':
            if player:
                player.die()
                self.players.remove(player)
            player = self.new_player(num)
        elif opcode == 'INPUT':
            player.process_input(payload)
        else:
            print("Unknown msg: " + opcode)
        return player

    async def tcp_socket_handler(self, reader, writer):
        num = PlayerActor.nplayers
        addr = writer.get_extra_info('peername')
        done = False
        player = None
        while not done:
            r, msg = await util.read_tcp_msg(reader)
            print("server got (%d) from %s: %s " % (r, addr, str(msg)))
            if r > 0:
                player = self.process_tcp_msg(msg, writer, player, num)
            else:
                done = True
        if UCAST:
            self.udp_peer_addr.pop(addr[0])
        writer.close()
        await writer.wait_closed()

    class UDPServerProtocol(DatagramProtocol):
        def __init__(self):
            super().__init__()
            self.transport = None

        def connection_made(self, transport):
            self.transport = transport
            print('UDP connection made')
            # sock = transport.get_extra_info("socket")
            # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        def datagram_received(self, data, addr):
            # message = data.decode()
            print('UDP datagram received %d from %s' % (len(data), addr))

    async def main(self):
        print("Starting TCP server")
        # default host is '0.0.0.0' = all interfaces
        tcp_server = await asyncio.start_server(self.tcp_socket_handler, port=TCP_PORT)

        local_addr = tcp_server.sockets[0].getsockname()
        print(f'Serving TCP on {local_addr}')

        print(f'Starting UDP server in {MODE_NAME} mode')
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        if BCAST:
            ## Considered unsafe
            ## sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Not all linux systems support this
            # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        elif MCAST:
            ttl = struct.pack('b', 1)  # Time-to-live
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        if BCAST or UCAST:
            sock.bind((LOCAL_IP, UDP_PORT))
        self.transport, protocol = await loop.create_datagram_endpoint(
            self.UDPServerProtocol, sock=sock)
            # allow_broadcast=BCAST,
            # local_addr=(LOCAL_IP, UDP_PORT))
        local_addr = self.transport.get_extra_info("sockname")
        print(f'Serving UDP on {local_addr}')

        pygame.font.init()  # for Score

        # Initialise clock
        clock = pygame.time.Clock()
        elapsed = 0
        try:
            while True:
                # Make sure game doesn't run at more than X frames per second
                elapsed += clock.tick(50)
                if elapsed >= 0.04:
                    self.pack_and_transmit()
                    elapsed = 0
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

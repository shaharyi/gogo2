from enum import Enum

TCP_PORT, UDP_PORT = 3000, 3001

WIDTH, HEIGHT = 640, 480
DEBUG = True

IMAGE_EXT = 'png'

MODE_INDEX = 0
MODE = 3 * [False]
MODE[MODE_INDEX] = True
UCAST, BCAST, MCAST = MODE
MODES = 'Unicast Broadcast Multicast'.split()
MODE_NAME = MODES[MODE.index(True)]

MCAST_GROUP = '225.0.0.250'
BCAST_IP = '192.168.1.255'  # local Broadcast ip
SERVER_TCP_LOCAL_ADDR = '0.0.0.0'  # all interfaces
ORIG_ANGLE = 90



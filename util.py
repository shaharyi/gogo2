from pdb import set_trace
import pickle
import struct

import pygame

from config import *

# logfile = open('/tmp/logs/%s.txt' % time.strftime('%Y%m%d_%H%M%S'), 'wt')
logfile = open('/tmp/gogo2.log', 'at')


def log(s):
    if not DEBUG: return
    logfile.write(s+'\n')    #logfile.write(os.linesep)
    logfile.flush()


def sign(x):
    return x > 0 and 1 or x < 0 and -1 or 0


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def prepare_msg(data):
    buf = pickle.dumps(data)
    len1 = len(buf)
    blen1 = struct.pack('i', len1)
    return blen1 + buf


def rotate(img, deg):
    """rotate image while keeping its center and size"""
    r = img.get_rect()
    s = pygame.transform.rotate(img, deg)
    r2 = s.get_rect()
    topleft = (r2.w - r.w)/2, (r2.h - r.h)/2
    new_surf = pygame.Surface(r.size)
    if pygame.get_init():
        new_surf.fill(img.get_colorkey())
        new_surf.set_colorkey(img.get_colorkey())
        new_surf = new_surf.convert()
    new_surf.blit(s, (0, 0), area=pygame.Rect(topleft, r.size))
    return new_surf


async def read_tcp_msg(reader):
    l = await reader.read(4)
    if len(l) <= 0:
        return 0, ''
    len1 = struct.unpack('i', l)[0]
    r = 0
    data = b''
    while r < len1:
        b = await reader.read(len1 - r)
        data += b
        r = len(data)
    msg = pickle.loads(data)
    return r, msg

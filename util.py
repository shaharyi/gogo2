import time

DEBUG = True

#logfile = open('/tmp/logs/%s.txt' % time.strftime('%Y%m%d_%H%M%S'), 'wt')
logfile = open('/tmp/gogo2.log', 'at')

IMAGE_EXT = 'png'


def log(s):
    if not DEBUG: return
    logfile.write(s+'\n')    #logfile.write(os.linesep)
    logfile.flush()


def sign(x):
    return x > 0 and 1 or x < 0 and -1 or 0

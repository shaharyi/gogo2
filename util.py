DEBUG = True

logfile = open('../logs/%s.txt' % time.strftime('%Y%m%d_%H%M%S'), 'wt')


def log(s):
    if not DEBUG: return
    logfile.write(s+'\n')    #logfile.write(os.linesep)
    logfile.flush()

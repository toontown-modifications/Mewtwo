from panda3d.core import loadPrcFile
import __builtin__, sys, os, traceback

loadPrcFile(''.join(sys.argv[1:]))

if os.path.exists('config/local.prc'):
    loadPrcFile('config/local.prc')

class game:
    name = 'server'
    process = 'server'
__builtin__.game = game

from game.otp.ai.AIBaseGlobal import *

if os.getenv('USE_EXT_AGENT') != 0:
    from ToontownServerRepositoryAgent import ToontownServerRepositoryAgent
    simbase.air = ToontownServerRepositoryAgent()

elif os.getenv('NO_EXT_AGENT'):
    from ToontownServerRepository import ToontownServerRepository
    simbase.air = ToontownServerRepository()

host = config.GetString('air-connect', '127.0.0.1')
port = 7100
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)

simbase.air.connect(host, port)

try:
    run()
except Exception:
    info = traceback.format_exc()

    with open('data/ud-traceback.txt', 'w+') as log:
        log.write(info + '\n')
    raise
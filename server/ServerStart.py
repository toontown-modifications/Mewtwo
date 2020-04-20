from panda3d.core import *
import __builtin__, sys, os

loadPrcFile(''.join(sys.argv[1:]))

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
    raise
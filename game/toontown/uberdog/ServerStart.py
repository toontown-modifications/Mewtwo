from panda3d.core import loadPrcFile
import __builtin__, sys, os, traceback

# Load our base configuration.
loadPrcFile(''.join(sys.argv[1:]))

if os.path.exists('config/local.prc'):
    # A local configuration exists, load it.
    loadPrcFile('config/local.prc')

class game:
    name = 'server'
    process = 'server'
__builtin__.game = game

from game.otp.ai.AIBaseGlobal import *

if os.getenv('USE_EXT_AGENT') != 0:
    # We want to use ExtAgent for messages.
    from ToontownServerRepositoryAgent import ToontownServerRepositoryAgent
    simbase.air = ToontownServerRepositoryAgent()

elif os.getenv('NO_EXT_AGENT'):
    # We want to use the OTP itself for messages.
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
    logFile = 'data/tracebacks/server/traceback.txt'

    with open(logFile, 'w+') as log:
        log.write(info + '\n')
    raise
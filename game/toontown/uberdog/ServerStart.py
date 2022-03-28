from panda3d.core import loadPrcFile, ConfigVariableString
from direct.showbase import PythonUtil
import builtins, sys, os, traceback

# Load our base configuration.
loadPrcFile(''.join(sys.argv[1:]))

if os.path.exists('config/local.prc'):
    # A local configuration exists, load it.
    loadPrcFile('config/local.prc')

class game:
    name = 'server'
    process = 'server'
builtins.game = game
builtins.isClient = lambda: PythonUtil.isClient()

from game.otp.uberdog.UberDogGlobal import *
from game.toontown.uberdog import PartiesUdConfig

uber.mysqlhost = ConfigVariableString("mysql-host", PartiesUdConfig.ttDbHost).getValue()

if os.getenv('USE_EXT_AGENT') == '1':
    # We want to use ExtAgent for messages.
    from .ToontownServerRepositoryAgent import ToontownServerRepositoryAgent
    uber.air = ToontownServerRepositoryAgent()
else:
    # We want to use the OTP itself for messages.
    from .ToontownServerRepository import ToontownServerRepository
    uber.air = ToontownServerRepository()

host = ConfigVariableString('air-connect', '127.0.0.1').getValue()
port = 7100
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)

uber.air.connect(host, port)

try:
    run()
except Exception:
    info = traceback.format_exc()
    logFile = 'data/tracebacks/server/traceback.txt'

    with open(logFile, 'w+') as log:
        log.write(info + '\n')
    raise
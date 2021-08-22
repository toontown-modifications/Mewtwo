from panda3d.core import loadPrcFile
from panda3d.toontown import DNAStorage, SuitLeg, SuitLegList
from direct.showbase import PythonUtil
import builtins, sys, os, traceback

builtins.isClient = lambda: PythonUtil.isClient()
builtins.DNAStorage = DNAStorage
builtins.SuitLeg = SuitLeg
builtins.SuitLegList = SuitLegList

# Load our base configuration.
loadPrcFile(''.join(sys.argv[1:]))

if os.path.exists('config/local.prc'):
    # A local configuration exists, load it.
    loadPrcFile('config/local.prc')

class game:
    name = 'toontown'
    process = 'server'

builtins.game = game

from game.otp.ai.AIBaseGlobal import *

from .ToontownAIRepository import ToontownAIRepository

districtName = os.getenv('DISTRICT_NAME')

simbase.air = ToontownAIRepository(int(os.getenv('BASE_CHANNEL')), districtName)

host = ConfigVariableString('air-connect', '127.0.0.1').value
port = 7100
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)

simbase.air.connect(host, port)

try:
    run()
except Exception:
    info = traceback.format_exc()
    logName = 'data/tracebacks/ai/{0}.txt'.format(districtName)

    with open(logName, 'w+') as log:
        log.write(info + '\n')
    raise
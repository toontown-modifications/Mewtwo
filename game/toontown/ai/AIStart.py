from panda3d.core import loadPrcFile
from panda3d.toontown import DNAStorage, SuitLeg, SuitLegList
from direct.showbase import PythonUtil
import __builtin__, sys, os, traceback

__builtin__.isClient = lambda: PythonUtil.isClient()
__builtin__.DNAStorage = DNAStorage
__builtin__.SuitLeg = SuitLeg
__builtin__.SuitLegList = SuitLegList

# Load our base configuration.
loadPrcFile(''.join(sys.argv[1:]))

if os.path.exists('config/local.prc'):
    # A local configuration exists, load it.
    loadPrcFile('config/local.prc')

class game:
    name = 'toontown'
    process = 'server'

__builtin__.game = game

from game.otp.ai.AIBaseGlobal import *

from ToontownAIRepository import ToontownAIRepository

districtName = os.getenv('DISTRICT_NAME')

simbase.air = ToontownAIRepository(int(os.getenv('BASE_CHANNEL')), districtName)

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
    logName = 'data/tracebacks/ai/{0}.txt'.format(districtName)

    with open(logName, 'w+') as log:
        log.write(info + '\n')
    raise
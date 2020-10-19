from panda3d.core import loadPrcFile
from panda3d.toontown import DNAStorage, SuitLeg, SuitLegList
import builtins, sys, os, traceback

builtins.isClient = lambda: PythonUtil.isClient()
builtins.DNAStorage = DNAStorage
builtins.SuitLeg = SuitLeg
builtins.SuitLegList = SuitLegList

loadPrcFile(''.join(sys.argv[1:]))

if os.path.exists('config/local.prc'):
    loadPrcFile('config/local.prc')

class game:
    name = 'toontown'
    process = 'server'

builtins.game = game

from game.otp.ai.AIBaseGlobal import *

from .ToontownAIRepository import ToontownAIRepository

simbase.air = ToontownAIRepository(int(os.getenv('BASE_CHANNEL')), os.getenv('DISTRICT_NAME'))

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

    with open('data/ai-traceback.txt', 'w+') as log:
        log.write(info + '\n')
    raise
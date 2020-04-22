from panda3d.core import *
from panda3d.toontown import DNAStorage, SuitLeg, SuitLegList
from direct.showbase import PythonUtil
import __builtin__, sys

__builtin__.isClient = lambda: PythonUtil.isClient()
__builtin__.DNAStorage = DNAStorage
__builtin__.SuitLeg = SuitLeg
__builtin__.SuitLegList = SuitLegList

loadPrcFile(''.join(sys.argv[1:]))

class game:
    name = 'toontown'
    process = 'server'

__builtin__.game = game

from game.otp.ai.AIBaseGlobal import *

from ToontownAIRepository import ToontownAIRepository

simbase.air = ToontownAIRepository()

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
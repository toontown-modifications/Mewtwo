from panda3d.core import *

from direct.showbase.ShowBase import *
from game.toontown.distributed import PythonUtil
import __builtin__

class Game:
    name = "toontown"

__builtin__.game = Game()
__builtin__.simbase = ShowBase()
__builtin__.process = 'ud'
__builtin__.isClient = lambda: PythonUtil.isClient()

from game.toontown.uberdog.ToontownUDRepository import ToontownUDRepository

simbase.air = ToontownUDRepository(config.GetInt('air-base-channel', 400000000),
                                   config.GetInt('air-stateserver', 1001))
                                   
host = config.GetString('air-connect', '162.246.19.251')
port = 7100
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)
simbase.air.connect(host, port)

try:
    run()
except SystemExit:
    raise
except Exception:
    info = PythonUtil.describeException()
    simbase.air.writeServerEvent('ai-exception', simbase.air.getAvatarIdFromSender(), simbase.air.getAccountIdFromSender(), info)
    raise
from panda3d.core import *

for dtool in ('children', 'parent', 'name'):
    del NodePath.DtoolClassDict[dtool]

from direct.showbase.ShowBase import *
from game.toontown.distributed import PythonUtil
import __builtin__, argparse

class Game:
    name = "toontown"

__builtin__.game = Game()
__builtin__.simbase = ShowBase()
__builtin__.process = 'ai'
__builtin__.isClient = lambda: PythonUtil.isClient()

parser = argparse.ArgumentParser()
parser.add_argument('--base-channel', help='The base channel that the server may use.')
parser.add_argument('--district-name', help="What this AI Server's district will be named.")
args = parser.parse_args()

localconfig = ''

if args.base_channel:
    localconfig += 'air-base-channel %s\n' % args.base_channel
if args.district_name:
    localconfig += 'district-name %s\n' % args.district_name

loadPrcFileData('Command-line', localconfig)

from game.toontown.ai.ToontownAIRepository import ToontownAIRepository

simbase.air = ToontownAIRepository(
    config.GetInt('air-base-channel', 401000000),
    config.GetInt('air-stateserver', 1001),
    config.GetString('district-name', 'Sillyville'))

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
    simbase.air.writeServerEvent('ai-exception',
                                 simbase.air.getAvatarIdFromSender(),
                                 simbase.air.getAccountIdFromSender(), info)
    raise
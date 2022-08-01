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

host = ConfigVariableString('air-connect', '127.0.0.1').getValue()
port = 7100
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)

simbase.air.connect(host, port)

try:
    run()
except:
    # Grab the exception data.
    info = traceback.format_exc()

    # Prepare the log name.
    logName = f'data/tracebacks/ai/{districtName}.txt'

    with open(logName, 'w+') as log:
        # Write this data to disk.
        log.write(info + '\n')
    raise
finally:
    isProdServer = ConfigVariableString('server-type', 'dev').getValue() == 'prod'

    if isProdServer:
        # Finally, send to to our Discord.
        from game.toontown.discord.Webhook import Webhook
        from game.toontown.uberdog.ExtAgent import ServerGlobals

        # Grab the server type.
        serverId = ServerGlobals.FINAL_TOONTOWN
        serverType = ServerGlobals.serverToName[serverId]

        # Let staff know this district is down.
        hookFields = [{
            'name': 'District Name',
            'value': districtName,
            'inline': True
        },
        {
            'name': 'Server Type',
            'value': serverType,
            'inline': True
        }]

        # Send this message to Discord.
        message = Webhook()
        message.setRequestType('post')
        message.setDescription('District has gone down!')
        message.setFields(hookFields)
        message.setColor(1127128)
        message.setWebhook(ConfigVariableString('discord-reset-webhook').getValue())
        message.finalize()
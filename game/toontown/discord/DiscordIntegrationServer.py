from direct.directnotify.DirectNotifyGlobal import directNotify
from twisted.internet import reactor, protocol
import _thread, json, base64

class DiscordIntegrationClient(protocol.Protocol):
    def connectionMade(self):
        self.server = self.factory

        self.server.clients.append(self)

    def dataReceived(self, data):
        data = json.loads(data)

        whatToDo = data['whatToDo']
        signature = data['signature']
        actualSignature = 'PleaseDoNotAbuseThisFunction'

        if signature != actualSignature:
            pass

        if whatToDo == 'kickRequest':
            avId = data['avId']
            reason = data['reason']
            simbase.air.extAgent.sendKick(avId, reason)
        elif whatToDo == 'systemMessage':
            message = data['message']
            channels = simbase.air.extAgent.clientChannel2avId

            for clientChannel in channels:
                simbase.air.extAgent.sendSystemMessage(clientChannel, message)

    def connectionLost(self, reason):
        self.server.clients.remove(self)

class DiscordIntegrationServer(protocol.ServerFactory):
    protocol = DiscordIntegrationClient

    notify = directNotify.newCategory('DiscordIntegrationServer')
    notify.setInfo(True)

    def __init__(self, air):
        self.air = air

        self.clients = []

        self.startServer()

    def setupTwisted(self):
        reactor.listenTCP(7199, self)
        reactor.run(installSignalHandlers = False)

    def startServer(self):
        thread = _thread.start_new_thread(self.setupTwisted, ())

        self.notify.info('Successfully started twisted server.')

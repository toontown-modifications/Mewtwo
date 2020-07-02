from direct.directnotify.DirectNotifyGlobal import directNotify

try:
    import _thread
except:
    import thread as _thread

import socket, json

class DiscordIntegrationServer:
    notify = directNotify.newCategory('DiscordIntegrationServer')
    notify.setInfo(True)

    def __init__(self, air):
        self.air = air

        self.startServer()

    def setupServer(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 7199))
        server.listen(10)

        while True:
            client, address = server.accept()
            data = client.recv(4096)

            data = json.loads(data)

            whatToDo = data['whatToDo']
            signature = data['signature']
            actualSignature = 'PleaseDoNotAbuseThisFunction'

            if signature != actualSignature:
                self.notify.info('Invalid signature: {0}!'.format(signature))
                return

            if whatToDo == 'kickRequest':
                avId = data['avId']
                reason = data['reason']
                simbase.air.extAgent.sendKick(avId, reason)
            elif whatToDo == 'systemMessage':
                message = data['message']
                channels = simbase.air.extAgent.clientChannel2avId

                for clientChannel in channels:
                    simbase.air.extAgent.sendSystemMessage(clientChannel, message)

    def startServer(self):
        thread = _thread.start_new_thread(self.setupServer, ())

        self.notify.info('Successfully started socket server.')
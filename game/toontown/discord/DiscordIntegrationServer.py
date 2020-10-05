from direct.directnotify.DirectNotifyGlobal import directNotify

import thread, socket, json

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
            client, ipAddress = server.accept()
            data = client.recv(4096)

            try:
                data = json.loads(data)
            except:
                # Skid, log the attempt.
                self.notify.warning('Client {0} tried to send non-JSON data!'.format(ipAddress))
                return

            whatToDo = data['whatToDo']
            signature = data['signature']
            actualSignature = config.GetString('discord-integration-sig')

            if signature != actualSignature:
                # Skid, log the attempt.
                self.notify.warning('Client {0} sent invalid signature: {0}!'.format(ipAddress, signature))
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
        serverThread = thread.start_new_thread(self.setupServer, ())

        self.notify.info('Successfully started socket server.')
from direct.directnotify.DirectNotifyGlobal import directNotify

import _thread, socket, json

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
                avId = int(data['avId'])
                reason = data['reason']
                simbase.air.extAgent.sendKick(avId, reason)
            elif whatToDo == 'banAccount':
                avatarId = int(data['avId'])

                def handleRetrieve(dclass, fields):
                    if dclass != simbase.air.dclassesByName['DistributedToonUD']:
                        return

                    accountId = fields['setDISLid'][0]
                    playToken = simbase.air.extAgent.accId2playToken.get(accountId, '')

                    simbase.air.extAgent.sendKick(avId, 'N/A')
                    simbase.air.extAgent.banAccount(playToken, 'N/A', 'N/A', True)

                # Query the avatar to get some account information.
                simbase.air.dbInterface.queryObject(simbase.air.dbId, avatarId, handleRetrieve)
            elif whatToDo == 'systemMessage':
                message = data['message']
                channels = simbase.air.extAgent.clientChannel2avId

                for clientChannel in channels:
                    simbase.air.extAgent.sendSystemMessage(clientChannel, message)
            elif whatToDo == 'approveName':
                avId = int(data['avId'])

                simbase.air.extAgent.approveName(avId)
            elif whatToDo == 'rejectName':
                avId = int(data['avId'])

                simbase.air.extAgent.rejectName(avId)

    def startServer(self):
        serverThread = _thread.start_new_thread(self.setupServer, ())

        self.notify.info('Successfully started socket server.')
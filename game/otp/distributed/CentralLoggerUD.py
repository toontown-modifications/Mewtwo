from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD

import json

class CentralLoggerUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory('CentralLoggerUD')
    notify.setInfo(True)

    def sendMessage(self, category, message, targetDISLid, targetAvId):
        self.notify.debug('Received message from client')

        parts = message.split('|')
        msgType = parts[0]
        fields = {
            'targetDISLid': targetDISLid,
            'targetAvId': targetAvId
        }

        print(msgType)

        if msgType == 'GUEST_FEEDBACK':
            fields['feedbackCategory'] = parts[1]
            fields['feedbackMessage'] = parts[2]

        if self.notify.getInfo():
            event = {
                'category': category,
                'message': message,
                'type': msgType,
            }
            event.update(fields)

            data = json.dumps(event)
            print(data)

        self.air.writeServerEvent(category, messageType = msgType, message = message, **fields)

    def logAIGarbage(self):
        pass

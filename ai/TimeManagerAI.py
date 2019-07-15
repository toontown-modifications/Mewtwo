from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObjectAI import DistributedObjectAI

import time

class TimeManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('TimeManagerAI')

    def requestServerTime(self, context):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        self.sendUpdateToAvatarId(avId, 'serverTime',
                                  [context, globalClockDelta.getRealNetworkTime(bits=32), int(time.time())])

    def setDisconnectReason(self, disconnectCode):
        pass
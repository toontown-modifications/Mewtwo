from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta

from game.otp.otpbase import OTPGlobals

import time

class TimeManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('TimeManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        # Dictionaries:
        self.avId2disconnectcode = {}
        self.avId2exceptioninfo = {}
        self.avId2CpuInfo = {}
        self.avId2cacheStatus = {}

    def requestServerTime(self, context):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        networkTime = globalClockDelta.getRealNetworkTime(bits = 32)
        currentTime = int(time.time())

        self.sendUpdateToAvatarId(avId, 'serverTime', [context, networkTime, currentTime])

    def setDisconnectReason(self, disconnectCode):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        reason = OTPGlobals.DisconnectReasons.get(disconnectCode, 'unknown')

        self.avId2disconnectcode[avId] = disconnectCode
        self.air.writeServerEvent('disconnect-reason', avId = avId, reason = reason)

    def setExceptionInfo(self, info):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        self.avId2exceptioninfo[avId] = info
        self.air.writeServerEvent('client-exception', avId = avId, info = info)

    def setSignature(self, userSignature, hBin, pycBin):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        self.sendUpdateToAvatarId(avId, 'setSignature', [userSignature, hBin, pycBin])

    def setFrameRate(self, todo0, todo1, todo2, todo3, todo4, todo5, todo6,
                     todo7, todo8, todo9, todo10, todo11, todo12, todo13,
                     todo14, todo15, todo16, todo17):
        pass

    def setCpuInfo(self, info, cacheStatus):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        self.avId2CpuInfo[avId] = info
        self.avId2cacheStatus[avId] = cacheStatus

    def checkForGarbageLeaks(self, todo0):
        pass

    def setNumAIGarbageLeaks(self, todo0):
        pass

    def setClientGarbageLeak(self, todo0, todo1):
        pass

    def checkAvOnDistrict(self, context, avId):
        av = self.air.doId2do.get(avId)

        if av:
            isOnShard = True
        else:
            isOnShard = False

        #self.sendUpdateToAvatarId(avId, 'checkAvOnDistrictResult', [context, avId, isOnShard])
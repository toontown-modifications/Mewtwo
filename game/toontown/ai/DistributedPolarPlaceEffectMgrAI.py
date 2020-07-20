from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.toontown.toonbase import ToontownGlobals
from game.toontown.ai.HolidayBaseAI import HolidayBaseAI

import time

class DistributedPolarPlaceEffectMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedPolarPlaceEffectMgrAI')

    def addPolarPlaceEffect(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return

        if av.getCheesyEffect()[0] != ToontownGlobals.CEBigWhite:
            expireTime = int(time.time() / 60 + 0.5) + 3600
            av.b_setCheesyEffect(ToontownGlobals.CEBigWhite, ToontownGlobals.TheBrrrgh, expireTime)

class PolarPlaceHolidayMgrAI(HolidayBaseAI):

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

        self.effectMgr = None

    def start(self):
        if not self.effectMgr:
            self.effectMgr = DistributedPolarPlaceEffectMgrAI(self.air)
            self.effectMgr.generateWithRequired(3821)

    def stop(self):
        if self.effectMgr:
            self.effectMgr.requestDelete()
            self.effectMgr = None
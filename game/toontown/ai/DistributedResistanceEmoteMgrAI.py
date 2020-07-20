from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.otp.otpbase.OTPLocalizer import EmoteFuncDict

from game.toontown.ai.HolidayBaseAI import HolidayBaseAI

class DistributedResistanceEmoteMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedResistanceEmoteMgrAI')

    def addResistanceEmote(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return

        if not av.emoteAccess[EmoteFuncDict['Resistance Salute']]:
            av.emoteAccess[EmoteFuncDict['Resistance Salute']] = 1
            av.b_setEmoteAccess(av.emoteAccess)

class ResistanceEmoteHolidayMgrAI(HolidayBaseAI):

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

        self.emoteMgr = None

    def start(self):
        if not self.emoteMgr:
            self.emoteMgr = DistributedResistanceEmoteMgrAI(self.air)
            self.emoteMgr.generateWithRequired(9720)

    def stop(self):
        if self.emoteMgr:
            self.emoteMgr.requestDelete()
            self.emoteMgr = None
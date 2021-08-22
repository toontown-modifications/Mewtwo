from .HolidayBaseAI import HolidayBaseAI
from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.ai.DistributedSillyMeterMgrAI import DistributedSillyMeterMgrAI
from game.toontown.toonbase import ToontownGlobals

class SillyMeterHolidayAI(HolidayBaseAI):
    notify = directNotify.newCategory('SillyMeterHolidayAI')
    FINAL_PHASE = 12

    def __init__(self, air, holidayId):
        HolidayBaseAI.__init__(self, air, holidayId)

        self.air.SillyMeterMgr = None

    def start(self):
        HolidayBaseAI.start(self)

        self.air.SillyMeterMgr = DistributedSillyMeterMgrAI(self.air, True, 0, 12, [])
        self.air.SillyMeterMgr.generateWithRequired(ToontownGlobals.UberZone)

        self.air.SillyMeterMgr.b_setCurPhase(self.FINAL_PHASE)
        self.air.SillyMeterMgr.b_setIsRunning(True)
        messenger.send('SillyMeterPhase', [self.FINAL_PHASE])

    def stop(self):
        HolidayBaseAI.stop(self)

        self.air.SillyMeterMgr.requestDelete()
        self.air.SillyMeterMgr = None
from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.ai.DistributedPhaseEventMgrAI import DistributedPhaseEventMgrAI

class DistributedSillyMeterMgrAI(DistributedPhaseEventMgrAI):
    notify = directNotify.newCategory('DistributedSillyMeterMgrAI')

    def __init__(self, air, curPhase, holidayDates, isRunning, numPhases):
        DistributedPhaseEventMgrAI.__init__(self, air, curPhase, holidayDates, isRunning, numPhases)
 
        air.SillyMeterMgr = self
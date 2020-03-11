from direct.directnotify import DirectNotifyGlobal
from game.toontown.ai.DistributedPhaseEventMgrAI import DistributedPhaseEventMgrAI


class DistributedHydrantZeroMgrAI(DistributedPhaseEventMgrAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedHydrantZeroMgrAI")

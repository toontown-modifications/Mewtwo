from direct.directnotify import DirectNotifyGlobal
from game.toontown.ai.DistributedPhaseEventMgrAI import DistributedPhaseEventMgrAI


class DistributedTrashcanZeroMgrAI(DistributedPhaseEventMgrAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedTrashcanZeroMgrAI")

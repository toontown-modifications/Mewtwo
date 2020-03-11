from direct.directnotify import DirectNotifyGlobal
from game.toontown.ai.DistributedPhaseEventMgrAI import DistributedPhaseEventMgrAI


class DistributedMailboxZeroMgrAI(DistributedPhaseEventMgrAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedMailboxZeroMgrAI")

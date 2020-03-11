from direct.directnotify import DirectNotifyGlobal
from game.toontown.estate.DistributedLawnDecorAI import DistributedLawnDecorAI


class DistributedGardenBoxAI(DistributedLawnDecorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedGardenBoxAI")

    def setTypeIndex(self, todo0):
        pass

from direct.directnotify import DirectNotifyGlobal
from game.toontown.estate.DistributedStatuaryAI import DistributedStatuaryAI


class DistributedChangingStatuaryAI(DistributedStatuaryAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedChangingStatuaryAI")

    def setGrowthLevel(self, todo0):
        pass

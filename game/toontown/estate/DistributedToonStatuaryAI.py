from direct.directnotify import DirectNotifyGlobal
from game.toontown.estate.DistributedStatuaryAI import DistributedStatuaryAI


class DistributedToonStatuaryAI(DistributedStatuaryAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedToonStatuaryAI")

    def setOptional(self, todo0):
        pass

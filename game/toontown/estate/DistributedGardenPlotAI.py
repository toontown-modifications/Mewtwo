from direct.directnotify import DirectNotifyGlobal
from game.toontown.estate.DistributedLawnDecorAI import DistributedLawnDecorAI


class DistributedGardenPlotAI(DistributedLawnDecorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedGardenPlotAI")

    def plantFlower(self, todo0, todo1):
        pass

    def plantGagTree(self, todo0, todo1):
        pass

    def plantStatuary(self, todo0):
        pass

    def plantToonStatuary(self, todo0, todo1):
        pass

    def plantNothing(self, todo0):
        pass

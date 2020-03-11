from direct.directnotify import DirectNotifyGlobal
from game.toontown.estate.DistributedStatuaryAI import DistributedStatuaryAI


class DistributedAnimatedStatuaryAI(DistributedStatuaryAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedAnimatedStatuaryAI")

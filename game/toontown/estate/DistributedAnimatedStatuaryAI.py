from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.estate.DistributedStatuaryAI import DistributedStatuaryAI

class DistributedAnimatedStatuaryAI(DistributedStatuaryAI):
    notify = directNotify.newCategory('DistributedAnimatedStatuaryAI')
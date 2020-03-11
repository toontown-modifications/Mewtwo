from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.classicchars.DistributedGoofySpeedwayAI import DistributedGoofySpeedwayAI
from game.toontown.toonbase import ToontownGlobals

class DistributedSuperGoofyAI(DistributedGoofySpeedwayAI):
    notify = directNotify.newCategory('DistributedSuperGoofyAI')

    def walkSpeed(self):
        return ToontownGlobals.SuperGoofySpeed
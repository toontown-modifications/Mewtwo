from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.classicchars.DistributedPlutoAI import DistributedPlutoAI
from game.toontown.toonbase import ToontownGlobals

class DistributedWesternPlutoAI(DistributedPlutoAI):
    notify = directNotify.newCategory('DistributedWesternPlutoAI')

    def walkSpeed(self):
        return ToontownGlobals.WesternPlutoSpeed
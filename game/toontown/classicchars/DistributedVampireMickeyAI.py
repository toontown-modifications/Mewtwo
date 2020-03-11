from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.classicchars.DistributedMickeyAI import DistributedMickeyAI
from game.toontown.toonbase import ToontownGlobals

class DistributedVampireMickeyAI(DistributedMickeyAI):
    notify = directNotify.newCategory('DistributedVampireMickeyAI')

    def walkSpeed(self):
        return ToontownGlobals.VampireMickeySpeed
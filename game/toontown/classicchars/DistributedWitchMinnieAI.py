from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.classicchars.DistributedMinnieAI import DistributedMinnieAI
from game.toontown.toonbase import ToontownGlobals

class DistributedWitchMinnieAI(DistributedMinnieAI):
    notify = directNotify.newCategory('DistributedWitchMinnieAI')

    def walkSpeed(self):
        return ToontownGlobals.WitchMinnieSpeed
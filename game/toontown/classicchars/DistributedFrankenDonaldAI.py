from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.classicchars.DistributedDonaldAI import DistributedDonaldAI

from game.toontown.toonbase import ToontownGlobals

class DistributedFrankenDonaldAI(DistributedDonaldAI):
    notify = directNotify.newCategory('DistributedFrankenDonaldAI')

    def walkSpeed(self):
        return ToontownGlobals.FrankenDonaldSpeed
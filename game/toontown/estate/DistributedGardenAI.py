from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.toontown.estate import HouseGlobals

class DistributedGardenAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedGardenAI')

    def isValidProp(self, prop):
        if not prop in (HouseGlobals.PROP_ICECUBE, HouseGlobals.PROP_FLOWER, HouseGlobals.PROP_SNOWFLAKE):
            return False

        return True

    def sendNewProp(self, prop, x, y, z):
        if not self.isValidProp(prop):
            return

        self.d_sendNewProp(avId, prop, x, y, z)

    def d_sendNewProp(self, avId, prop, x, y, z):
        self.sendUpdate('sendNewProp', [prop, x, y, z])
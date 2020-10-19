from direct.directnotify import DirectNotifyGlobal
from . import HoodDataAI
from game.toontown.toonbase import ToontownGlobals
from game.toontown.safezone import DistributedTrolleyAI
from game.toontown.safezone import DGTreasurePlannerAI
from game.toontown.classicchars import DistributedGoofyAI
from game.toontown.classicchars import DistributedDaisyAI
from game.toontown.safezone import DistributedDGFlowerAI
from game.toontown.safezone import ButterflyGlobals

class DGHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DGHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DaisyGardens
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)
        self.treasurePlanner = DGTreasurePlannerAI.DGTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        self.classicChar = DistributedDaisyAI.DistributedDaisyAI(self.air)
        self.classicChar.generateWithRequired(self.zoneId)
        self.classicChar.start()
        self.addDistObj(self.classicChar)
        flower = DistributedDGFlowerAI.DistributedDGFlowerAI(self.air)
        flower.generateWithRequired(self.zoneId)
        flower.start()
        self.addDistObj(flower)
        self.createButterflies(ButterflyGlobals.DG)

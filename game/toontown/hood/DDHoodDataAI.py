from direct.directnotify import DirectNotifyGlobal
import HoodDataAI
from game.toontown.toonbase import ToontownGlobals
from game.toontown.safezone import DistributedTrolleyAI
from game.toontown.safezone import DDTreasurePlannerAI
from game.toontown.safezone import DistributedBoatAI
from game.toontown.classicchars import DistributedDonaldDockAI

class DDHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DDHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DonaldsDock
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
        self.treasurePlanner = DDTreasurePlannerAI.DDTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        boat = DistributedBoatAI.DistributedBoatAI(self.air)
        boat.generateWithRequired(self.zoneId)
        boat.start()
        self.addDistObj(boat)
        self.classicChar = DistributedDonaldDockAI.DistributedDonaldDockAI(self.air)
        self.classicChar.generateWithRequired(self.zoneId)
        self.classicChar.start()
        self.addDistObj(self.classicChar)

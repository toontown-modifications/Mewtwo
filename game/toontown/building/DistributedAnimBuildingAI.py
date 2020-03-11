from direct.directnotify import DirectNotifyGlobal
from game.toontown.building import DistributedBuildingAI
from game.toontown.building import DistributedAnimDoorAI
from game.toontown.building import DoorTypes

class DistributedAnimBuildingAI(DistributedBuildingAI.DistributedBuildingAI):

    def __init__(self, air, blockNumber, zoneId, trophyMgr):
        DistributedBuildingAI.DistributedBuildingAI.__init__(self, air, blockNumber, zoneId, trophyMgr)

    def createExteriorDoor(self):
        result = DistributedAnimDoorAI.DistributedAnimDoorAI(self.air, self.block, DoorTypes.EXT_ANIM_STANDARD)
        return result

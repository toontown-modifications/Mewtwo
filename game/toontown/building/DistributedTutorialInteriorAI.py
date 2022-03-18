from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

from game.toontown.toon import NPCToons


class DistributedTutorialInteriorAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTutorialInteriorAI')

    def __init__(self, block, air, zoneId, building, npcId):
        """blockNumber: the landmark building number (from the name)"""
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId
        self.building = building
        self.tutorialNpcId = npcId

        # Make any npcs that may be in this interior zone
        # If there are none specified, this will just be an empty list
        self.npcs = NPCToons.createNpcsInZone(air, zoneId)

    def delete(self):
        self.ignoreAll()
        for npc in self.npcs:
            npc.requestDelete()
        del self.npcs
        del self.building
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getZoneIdAndBlock(self):
        return [self.zoneId, self.block]

    def getTutorialNpcId(self):
        return self.tutorialNpcId
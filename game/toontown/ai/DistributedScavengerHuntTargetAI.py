from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedScavengerHuntTargetAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedScavengerHuntTargetAI')

    def __init__(self, air, holidayMgr):
        DistributedObjectAI.__init__(self, air)

        self.holidayMgr = holidayMgr

    def attemptScavengerHunt(self):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        toon = self.air.doId2do.get(avId)

        if not toon:
            message = f'Unknown player {avId} tried to attempt scavenger hunt!'
            self.notify.warning(message)
            self.air.writeServerEvent('suspicious', avId, message)
            return

        self.holidayMgr.attemptScavengerHunt(toon, self.zoneId)
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

HealFrequency = 30.0 # The time in seconds between each Toon-up pulse.

class SafeZoneManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('SafeZoneManagerAI')

    def enterSafeZone(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            return

        # Start healing this avatar.
        av.startToonUp(HealFrequency)

        # Used for avatars that are in battle in case they escape.
        event = 'inSafezone-{0}'.format(avId)
        messenger.send(event)

    def exitSafeZone(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            return

        # Stop healing this avatar.
        av.stopToonUp()
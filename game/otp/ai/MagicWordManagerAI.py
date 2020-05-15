from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify.DirectNotifyGlobal import directNotify

class MagicWordManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('MagicWordManagerAI')

    def setMagicWord(self, magicWord, avId, zoneId):
        invokerId = self.air.getAvatarIdFromSender()
        invoker = self.air.doId2do.get(invokerId)

        if not invoker:
            self.sendUpdateToAvatarId(invokerId, 'setMagicWordResponse', ['Missing invoker!'])
            return

        target = self.air.doId2do.get(avId)

        if not target:
            self.sendUpdateToAvatarId(invokerId, 'setMagicWordResponse', ['Missing target!'])
            return

        self.notify.info('{0} with avId of {1} succesfully executed Magic Word: {2}!'.format(invoker.getName(), invokerId, magicWord))

    def setWho(self, avIds = []):
        pass

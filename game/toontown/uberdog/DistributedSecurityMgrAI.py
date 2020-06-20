from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI

class DistributedSecurityMgrAI(DistributedObjectGlobalAI):
    notify = directNotify.newCategory('DistributedSecurityMgrAI')

    def requestAccountId(self, avId, callback):
        if self.notify.getDebug():
            self.notify.debug('Got avId: {0} and callback {1}.'.format(avId, callback))

        accId = self.air.GetAccountIDFromChannelCode(avId)

        return accId

    def requestAccountIdResponse(self, todo0, todo1):
        pass

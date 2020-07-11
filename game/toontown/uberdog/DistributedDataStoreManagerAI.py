from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI

from game.otp.distributed import OtpDoGlobals

import cPickle

class DistributedDataStoreManagerAI(DistributedObjectGlobalAI):
    notify = directNotify.newCategory('DistributedDataStoreManagerAI')

    context = 0
    ctx2Callback = {}

    def startStore(self, typeId):
        self.sendUpdate('startStore', [typeId])

    def stopStore(self, typeId):
        self.sendUpdate('stopStore', [typeId])

    def queryStore(self, query, callback):
        if type(query) != str:
            return

        self.context += 1
        self.ctx2Callback[self.context] = callback
        self.sendUpdate('queryStore', [self.context, query])

    def receiveResults(self, context, results):
        callback = self.ctx2Callback.get(context)

        if not callback:
            self.notify.warning('Got receiveResults with unknown context: {0}'.format(context))
            return

        results = cPickle.loads(results)
        callback(results)
        del self.ctx2Callback[context]

    def deleteBackupStores(self):
        self.sendUpdate('deleteBackupStores')
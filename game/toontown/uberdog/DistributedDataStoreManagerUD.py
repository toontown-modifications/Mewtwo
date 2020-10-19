from datetime import datetime

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD

from .ScavengerHuntDataStore import ScavengerHuntDataStore

import os

type2Filename = {
    1: 'trickOrTreat',
    2: 'winterCaroling'
}

class DistributedDataStoreManagerUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory('DistributedDataStoreManagerUD')
    serverDataFolder = simbase.config.GetString('server-data-folder', '')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)

        self.dataStore = None
        self.activeType = 0

    def startStore(self, typeId):
        if self.dataStore:
            return

        filename = type2Filename.get(typeId)

        if not filename:
            self.notify.warning('Got unknown type: {}'.format(typeId))

        self.dataStore = ScavengerHuntDataStore(self.serverDataFolder + filename)
        self.typeId = typeId

    def stopStore(self, typeId):
        if not self.dataStore and typeId != self.typeId:
            return

        self.dataStore.destroy()
        self.dataStore = None

    def queryStore(self, context, query):
        sender = self.air.getMsgSender()

        if not self.dataStore:
            self.notify.warning('Got queryStore from {} while dataStore is None!'.format(sender))
            return

        results = self.dataStore.query(query)

        self.sendUpdateToChannel(sender, 'receiveResults', [context, results])

    def deleteBackupStores(self):
        pass
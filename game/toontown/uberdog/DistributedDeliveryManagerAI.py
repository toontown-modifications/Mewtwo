from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI

from game.toontown.catalog import CatalogItem


class DistributedDeliveryManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedDeliveryManagerAI')

    def sendDeliverGifts(self, avId, now):
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        _, remainingGifts = av.onGiftOrder.extractDeliveryItems(now)
        av.sendUpdate('setGiftSchedule',
                      [remainingGifts.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)])

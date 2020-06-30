# uncompyle6 version 3.7.1
# Python bytecode 2.4 (62061)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  4 2019, 01:37:19) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: toontown.catalog.CatalogManager
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal

class CatalogManager(DistributedObject.DistributedObject):
    __module__ = __name__
    notify = DirectNotifyGlobal.directNotify.newCategory('CatalogManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        if base.cr.catalogManager != None:
            base.cr.catalogManager.delete()
        base.cr.catalogManager = self
        DistributedObject.DistributedObject.generate(self)
        if hasattr(base.localAvatar, 'catalogScheduleNextTime') and base.localAvatar.catalogScheduleNextTime == 0:
            self.d_startCatalog()
        return

    def disable(self):
        base.cr.catalogManager = None
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        base.cr.catalogManager = None
        DistributedObject.DistributedObject.delete(self)
        return

    def d_startCatalog(self):
        self.sendUpdate('startCatalog', [])
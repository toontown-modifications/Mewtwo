# uncompyle6 version 3.7.1
# Python bytecode 2.4 (62061)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  4 2019, 01:37:19) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: toontown.catalog.CatalogAnimatedFurnitureItem
from CatalogFurnitureItem import *
FTAnimRate = 6
AnimatedFurnitureItemKeys = (10020, 270, 990, 460, 470, 480, 490, 491, 492)

class CatalogAnimatedFurnitureItem(CatalogFurnitureItem):
    __module__ = __name__

    def loadModel(self):
        model = CatalogFurnitureItem.loadModel(self)
        self.setAnimRate(model, self.getAnimRate())
        return model

    def getAnimRate(self):
        item = FurnitureTypes[self.furnitureType]
        if FTAnimRate < len(item):
            animRate = item[FTAnimRate]
            if not animRate == None:
                return item[FTAnimRate]
            else:
                return 1
        else:
            return 1
        return

    def setAnimRate(self, model, rate):
        seqNodes = model.findAllMatches('**/seqNode*')
        for seqNode in seqNodes.asList():
            seqNode.node().setPlayRate(rate)
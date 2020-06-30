# uncompyle6 version 3.7.1
# Python bytecode 2.4 (62061)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  4 2019, 01:37:19) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: toontown.catalog.CatalogSurfaceItem
import CatalogItem, CatalogAtticItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from CatalogSurfaceColors import *
STWallpaper = 0
STMoulding = 1
STFlooring = 2
STWainscoting = 3
NUM_ST_TYPES = 4

class CatalogSurfaceItem(CatalogAtticItem.CatalogAtticItem):
    __module__ = __name__

    def makeNewItem(self):
        CatalogAtticItem.CatalogAtticItem.makeNewItem(self)

    def setPatternIndex(self, patternIndex):
        self.patternIndex = patternIndex

    def setColorIndex(self, colorIndex):
        self.colorIndex = colorIndex

    def saveHistory(self):
        return 1

    def recordPurchase(self, avatar, optional):
        self.giftTag = None
        (house, retcode) = self.getHouseInfo(avatar)
        if retcode >= 0:
            house.addWallpaper(self)
        return retcode

    def getDeliveryTime(self):
        return 60
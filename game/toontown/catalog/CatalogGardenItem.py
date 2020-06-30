# uncompyle6 version 3.7.1
# Python bytecode 2.4 (62061)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  4 2019, 01:37:19) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: toontown.catalog.CatalogGardenItem
import CatalogItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from direct.interval.IntervalGlobal import *
from toontown.estate import GardenGlobals

class CatalogGardenItem(CatalogItem.CatalogItem):
    __module__ = __name__
    sequenceNumber = 0

    def makeNewItem(self, itemIndex=0, count=3, tagCode=1):
        self.gardenIndex = itemIndex
        self.numItems = count
        self.giftCode = tagCode
        CatalogItem.CatalogItem.makeNewItem(self)

    def getPurchaseLimit(self):
        if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
            return 1
        else:
            return 100

    def reachedPurchaseLimit(self, avatar):
        if self in avatar.onOrder or self in avatar.mailboxContents or self in avatar.onGiftOrder or self in avatar.awardMailboxContents or self in avatar.onAwardOrder:
            return 1
        return 0

    def getAcceptItemErrorText(self, retcode):
        if retcode == ToontownGlobals.P_ItemAvailable:
            return TTLocalizer.CatalogAcceptGarden
        return CatalogItem.CatalogItem.getAcceptItemErrorText(self, retcode)

    def saveHistory(self):
        return 1

    def getTypeName(self):
        return TTLocalizer.GardenTypeName

    def getName(self):
        name = GardenGlobals.Specials[self.gardenIndex]['photoName']
        return name

    def recordPurchase(self, avatar, optional):
        if avatar:
            avatar.addGardenItem(self.gardenIndex, self.numItems)
        return ToontownGlobals.P_ItemAvailable

    def getPicture(self, avatar):
        photoModel = GardenGlobals.Specials[self.gardenIndex]['photoModel']
        beanJar = loader.loadModel(photoModel)
        frame = self.makeFrame()
        beanJar.reparentTo(frame)
        photoPos = GardenGlobals.Specials[self.gardenIndex]['photoPos']
        beanJar.setPos(*photoPos)
        photoScale = GardenGlobals.Specials[self.gardenIndex]['photoScale']
        beanJar.setScale(photoScale)
        self.hasPicture = True
        return (frame, None)

    def output(self, store=-1):
        return 'CatalogGardenItem(%s%s)' % (self.gardenIndex, self.formatOptionalData(store))

    def compareTo(self, other):
        return 0

    def getHashContents(self):
        return self.gardenIndex

    def getBasePrice(self):
        beanCost = GardenGlobals.Specials[self.gardenIndex]['beanCost']
        return beanCost

    def decodeDatagram(self, di, versionNumber, store):
        CatalogItem.CatalogItem.decodeDatagram(self, di, versionNumber, store)
        self.gardenIndex = di.getUint8()
        self.numItems = di.getUint8()

    def encodeDatagram(self, dg, store):
        CatalogItem.CatalogItem.encodeDatagram(self, dg, store)
        dg.addUint8(self.gardenIndex)
        dg.addUint8(self.numItems)

    def getRequestPurchaseErrorText(self, retcode):
        retval = CatalogItem.CatalogItem.getRequestPurchaseErrorText(self, retcode)
        origText = retval
        if retval == TTLocalizer.CatalogPurchaseItemAvailable or retval == TTLocalizer.CatalogPurchaseItemOnOrder:
            recipeKey = GardenGlobals.getRecipeKeyUsingSpecial(self.gardenIndex)
            if not recipeKey == -1:
                retval += GardenGlobals.getPlantItWithString(self.gardenIndex)
                if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
                    if GardenGlobals.ACCELERATOR_USED_FROM_SHTIKER_BOOK:
                        retval = origText
                        retval += TTLocalizer.UseFromSpecialsTab
                    retval += TTLocalizer.MakeSureWatered
        return retval

    def getRequestPurchaseErrorTextTimeout(self):
        return 20

    def getDeliveryTime(self):
        if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
            return 24 * 60
        else:
            return 0

    def getPurchaseLimit(self):
        if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
            return 1
        else:
            return 0

    def compareTo(self, other):
        if self.gardenIndex != other.gardenIndex:
            return self.gardenIndex - other.gardenIndex
        return self.gardenIndex - other.gardenIndex

    def reachedPurchaseLimit(self, avatar):
        if avatar.onOrder.count(self) != 0:
            return 1
        if avatar.mailboxContents.count(self) != 0:
            return 1
        for specials in avatar.getGardenSpecials():
            if specials[0] == self.gardenIndex:
                if self.gardenIndex == GardenGlobals.GardenAcceleratorSpecial:
                    return 1

        return 0

    def isSkillTooLow(self, avatar):
        recipeKey = GardenGlobals.getRecipeKeyUsingSpecial(self.gardenIndex)
        recipe = GardenGlobals.Recipes[recipeKey]
        numBeansRequired = len(recipe['beans'])
        canPlant = avatar.getBoxCapability()
        result = False
        if canPlant < numBeansRequired:
            result = True
        if not result and GardenGlobals.Specials.has_key(self.gardenIndex) and GardenGlobals.Specials[self.gardenIndex].has_key('minSkill'):
            minSkill = GardenGlobals.Specials[self.gardenIndex]['minSkill']
            if avatar.shovelSkill < minSkill:
                result = True
            else:
                result = False
        return result

    def noGarden(self, avatar):
        return not avatar.getGardenStarted()

    def isGift(self):
        return 0
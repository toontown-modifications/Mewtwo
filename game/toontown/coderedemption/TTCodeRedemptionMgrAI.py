from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.toontown.toonbase import ToontownGlobals

from game.toontown.coderedemption import TTCodeRedemptionConsts
from game.toontown.rpc import AwardManagerConsts

# Catalog Imports
from game.toontown.catalog import CatalogItem
from game.toontown.catalog.CatalogItemList import CatalogItemList
from game.toontown.catalog.CatalogPoleItem import CatalogPoleItem
from game.toontown.catalog.CatalogBeanItem import CatalogBeanItem
from game.toontown.catalog.CatalogChatItem import CatalogChatItem
from game.toontown.catalog.CatalogClothingItem import CatalogClothingItem, getAllClothes
from game.toontown.catalog.CatalogAccessoryItem import CatalogAccessoryItem
from game.toontown.catalog.CatalogRentalItem import CatalogRentalItem
from game.toontown.catalog.CatalogInvalidItem import CatalogInvalidItem
from game.toontown.catalog.CatalogFurnitureItem import CatalogFurnitureItem

import time

class TTCodeRedemptionMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('TTCodeRedemptionMgrAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.air = air

        self.failedAttempts = 0
        self.maxCodeAttempts = config.GetInt('max-code-redemption-attempts', 5)

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

    def delete(self):
        DistributedObjectAI.delete(self)

    def giveAwardToToonResult(self, todo0, todo1):
        pass

    def d_redeemCodeResult(self, avId, context, result, awardMgrResult):
        self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, result, awardMgrResult])

    def redeemCode(self, context, code):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Tried to redeem a code from an invalid avId')
            return

        av = self.air.doId2do.get(avId)

        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Invalid avatar tried to redeem a code')
            return

        # Do we want coderedemption?
        if not self.air.wantCodeRedemption:
            result = TTCodeRedemptionConsts.RedeemErrors.SystemUnavailable
            awardMgrResult = 0

        if self.failedAttempts > self.maxCodeAttempts:
            result = TTCodeRedemptionConsts.RedeemErrors.TooManyAttempts
            awardMgrResult = 0
            self.failedAttempts = 0

        # Iterate over these items and deliver item to player.
        items = self.getItemsForCode(code)

        if not items:
            # This code is not valid.
            result = TTCodeRedemptionConsts.RedeemErrors.CodeDoesntExist
            awardMgrResult = AwardManagerConsts.GiveAwardErrors.Success
            self.failedAttempts += 1
            self.d_redeemCodeResult(avId, context, result, awardMgrResult)
            return

        # This code is valid.
        for item in items:
            if isinstance(item, CatalogInvalidItem): # Invalid item.
                self.air.writeServerEvent('suspicious', avId = avId, issue = 'Invalid CatalogItem\'s for code: %s' % code)
                result = TTCodeRedemptionConsts.RedeemErrors.CodeDoesntExist
                awardMgrResult = 0
                break

        if len(av.mailboxContents) + len(av.onGiftOrder) >= ToontownGlobals.MaxMailboxContents:
            # Mailbox is full
            result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
            awardMgrResult = AwardManagerConsts.GiveAwardErrors.FullMailbox
        else:
            limited = item.reachedPurchaseLimit(av)
            notOfferedTo = item.notOfferedTo(av)

            if notOfferedTo:
                # Toon is not the correct gender for this item.
                result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.WrongGender

            elif limited == 0:
                 # Success, lets deliver the item.
                item.deliveryDate = int(time.time() / 60) + 1 # Let's just deliver the item right away.
                av.onOrder.append(item)
                av.b_setDeliverySchedule(av.onOrder)
                result = TTCodeRedemptionConsts.RedeemErrors.Success
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.Success
                self.air.writeServerEvent('code-redeemed', avId = avId, issue = 'Successfuly redeemed code: {0}'.format(code))
            elif limited == 1:
                result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyInOrderedQueue
                self.air.writeServerEvent('code-redeemed', avId = avId, issue = 'Could not deliver items for code: {0}'.format(code))
            elif limited == 2:
                result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyInMailbox
                self.air.writeServerEvent('code-redeemed', avId = avId, issue = 'Could not deliver items for code: {0}'.format(code))
            elif limited == 3:
                result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyBeingWorn
                self.air.writeServerEvent('code-redeemed', avId = avId, issue = 'Could not deliver items for code: {0}'.format(code))
            elif limited == 4:
                result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyInCloset
                self.air.writeServerEvent('code-redeemed', avId = avId, issue = 'Could not deliver items for code: {0}'.format(code))

        # Send our response.
        self.d_redeemCodeResult(avId, context, result, awardMgrResult)

    def getItemsForCode(self, code):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Could not parse the gender of an invalid avId')
            return

        av = self.air.doId2do.get(avId)

        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Could not parse the gender of an invalid avatar')
            return

        '''
        # Here is an example of giving clothing to specific genders.
        if code == 'GenderExample':
            # The following code will check to see if the gender is a male.
            # If it is, then they will be given shirt 2002.
            if av.getStyle().getGender() == 'm':
                shirt = CatalogClothingItem(2002, 0)
            # If it sees the gender isn't male, it will give shirt 2003.
            else:
                shirt = CatalogClothingItem(2003, 0)
            return [shirt]
        '''

        code = code.lower() # Anti-frustration features, activate!

        # Our codes.
        if code == 'gadzooks':
            shirt = CatalogClothingItem(1807, 0)
            return [shirt]

        if code == 'sillymeter' or code == 'silly meter' or code == 'silly-meter':
            shirt = CatalogClothingItem(1753, 0)
            return [shirt]

        if code == 'gc-sbfo' or code == 'gc sbfo' or code == 'gcsbfo':
            shirt = CatalogClothingItem(1788, 0)
            return [shirt]

        if code == 'getconnected' or code == 'get connected' or code == 'get_connected':
            shirt = CatalogClothingItem(1752, 0)
            return [shirt]

        if code == 'summer':
            shirt = CatalogClothingItem(1709, 0)
            return [shirt]

        if code == 'brrrgh':
            shirt = CatalogClothingItem(1800, 0)
            return [shirt]

        if code == 'toontastic':
            shirt = CatalogClothingItem(1820, 0)
            return [shirt]

        if code == 'sunburst':
            shirt = CatalogClothingItem(1809, 0)
            return [shirt]

        if code == 'sweet':
            beans = CatalogBeanItem(12000, tagCode = 2)
            return [beans]

        if code == 'tasty':
            beans = CatalogBeanItem(12000, tagCode = 2)
            return [beans]

        if code == 'beaned':
            beans = CatalogBeanItem(12000, tagCode = 2)
            return [beans]

        if code == 'winter' or code == 'cannons':
            rent = CatalogRentalItem(ToontownGlobals.RentalCannon, 48 * 60, 0)
            return [rent]

        if code == 'gadzooks':
            shirt = CatalogClothingItem(1807, 0)
            return [shirt]

        if code == 'spooky':
            shirt = CatalogClothingItem(1799, 0)
            return [shirt]

        if code == 'doodle':
            shirt = CatalogClothingItem(1746, 0)
            return [shirt]

        if code == 'trunk':
            if av.getStyle().getGender() == 'm':
                trunk = CatalogFurnitureItem(4000, 0)
            else:
                shirt = CatalogFurnitureItem(4010, 0)
            return [trunk]

        return False

    def requestCodeRedeem(self, todo0, todo1):
        pass

    def redeemCodeResult(self, todo0, todo1, todo2):
        pass
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.toontown.toonbase import ToontownGlobals

from game.toontown.coderedemption import TTCodeRedemptionConsts

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

import time

class TTCodeRedemptionMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('TTCodeRedemptionMgrAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.air = air

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

    def delete(self):
        DistributedObjectAI.delete(self)

    def giveAwardToToonResult(self, todo0, todo1):
        pass

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
            self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, TTCodeRedemptionConsts.RedeemErrors.SystemUnavailable, 0])
            return
        
        # Constants
        delivered = False

        # Iterate over these items and deliver item to player.
        items = self.getItemsForCode(code)

        for item in items:
            if isinstance(item, CatalogInvalidItem): # Invalid item.
                self.air.writeServerEvent('suspicious', avId=avId, issue='Invalid CatalogItem\'s for code: %s' % code)
                self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, TTCodeRedemptionConsts.RedeemErrors.CodeDoesntExist, 0])
                break

            if len(av.mailboxContents) + len(av.onGiftOrder) >= ToontownGlobals.MaxMailboxContents:
                # Mailbox is full
                delivered = False
                break

            item.deliveryDate = int(time.time() / 60) + 1 # Let's just deliver the item right away.
            av.onOrder.append(item)
            av.b_setDeliverySchedule(av.onOrder)
            delivered = True

        if not delivered:
            # 0 is Success
            # 1, 2, 15, & 16 is an UnknownError
            # 3 & 4 is MailboxFull
            # 5 & 10 is AlreadyInMailbox
            # 6, 7, & 11 is AlreadyInQueue
            # 8 is AlreadyInCloset
            # 9 is AlreadyBeingWorn
            # 12, 13, & 14 is AlreadyReceived
            self.air.writeServerEvent('code-redeemed', avId = avId, issue = 'Could not deliver items for code: %s' % code)
            self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, TTCodeRedemptionConstants.RedeemErrors.AwardCouldntBeGiven, 0])
            return

        # Send the item and tell the user its A-Okay
        self.air.writeServerEvent('code-redeemed', avId=avId, issue='Successfuly redeemed code: %s' % code)
        self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, TTCodeRedemptionConsts.RedeemErrors.Success, 0])

    def getItemsForCode(self, code):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            self.air.writeServerEvent('suspicious', avId = avId, issue='Could not parse the gender of an invalid avId')
            return

        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue='Could not parse the gender of an invalid avatar')
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

        return []

    def requestCodeRedeem(self, todo0, todo1):
        pass

    def redeemCodeResult(self, todo0, todo1, todo2):
        pass

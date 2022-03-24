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

from game.toontown.uberdog.ExtAgent import ServerGlobals

import time, requests, json

class TTCodeRedemptionMgrAI(DistributedObjectAI):
    notify = directNotify.newCategory('TTCodeRedemptionMgrAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.air = air

        self.failedAttempts = 0
        self.maxCodeAttempts = config.GetInt('max-code-redemption-attempts', 5)

        self.webHeaders = {
            'User-Agent': 'SunriseGames-TTCodeRedemptionMgrAI'
        }

    def d_redeemCodeResult(self, avId, context, result, awardMgrResult):
        self.sendUpdateToAvatarId(avId, 'redeemCodeResult', [context, result, awardMgrResult])

    def redeemCode(self, context, code):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            # Invalid avatar id.
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Tried to redeem a code from an invalid avId')
            return

        av = self.air.doId2do.get(avId)

        if not av:
            # Invalid avatar.
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Invalid avatar tried to redeem a code')
            return

        # Check to see if redemption is enabled.
        if not self.air.wantCodeRedemption:
            result = TTCodeRedemptionConsts.RedeemErrors.SystemUnavailable
            awardMgrResult = 0

        # Check to see if this avatar has attempted redemption too many times.
        if self.failedAttempts > self.maxCodeAttempts:
            # We have attempted to redeem too many times.
            result = TTCodeRedemptionConsts.RedeemErrors.TooManyAttempts
            awardMgrResult = 0
            self.failedAttempts = 0

        # Make the code lowercase.
        code = code.lower()

        # Iterate over these items and deliver item to player.
        items = self.getItemsForCode(code)

        if not items:
            # This code is not valid.
            result = TTCodeRedemptionConsts.RedeemErrors.CodeDoesntExist
            awardMgrResult = AwardManagerConsts.GiveAwardErrors.Success
            self.failedAttempts += 1
            self.d_redeemCodeResult(avId, context, result, awardMgrResult)
            return

        # Has this avatar already redeemed this code?
        if self.air.isProdServer() and str(avId) in self.getCodeRedeemers(code):
            # Yup!
            result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
            awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyRented
            self.d_redeemCodeResult(avId, context, result, awardMgrResult)
            return

        # Check to see if the items in the code are valid.
        for item in items:
            if isinstance(item, CatalogInvalidItem):
                # This item is invalid.
                self.air.writeServerEvent('suspicious', avId = avId, issue = f'Invalid CatalogItem\'s for code: {code}')
                result = TTCodeRedemptionConsts.RedeemErrors.CodeDoesntExist
                awardMgrResult = 0
                break

            if len(av.mailboxContents) + len(av.onGiftOrder) >= ToontownGlobals.MaxMailboxContents:
                # Our mailbox is full.
                result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                awardMgrResult = AwardManagerConsts.GiveAwardErrors.FullMailbox
            else:
                # Check to see if the avatar can use this code.
                limited = item.reachedPurchaseLimit(av)
                notOfferedTo = item.notOfferedTo(av)

                if notOfferedTo:
                    # Toon is not the correct gender for this item.
                    result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                    awardMgrResult = AwardManagerConsts.GiveAwardErrors.WrongGender

                elif limited == 0:
                    # Success, lets deliver the item right away.
                    item.deliveryDate = int(time.time() / 60) + 1
                    item.specialEventId = 1
                    av.onAwardOrder.append(item)
                    av.b_setAwardSchedule(av.onAwardOrder)
                    result = TTCodeRedemptionConsts.RedeemErrors.Success
                    self.setRedeemedCode(code, avId)
                    awardMgrResult = AwardManagerConsts.GiveAwardErrors.Success
                elif limited == 1:
                    result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                    awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyInOrderedQueue
                elif limited == 2:
                    result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                    awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyInMailbox
                elif limited == 3:
                    result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                    awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyBeingWorn
                elif limited == 4:
                    result = TTCodeRedemptionConsts.RedeemErrors.AwardCouldntBeGiven
                    awardMgrResult = AwardManagerConsts.GiveAwardErrors.AlreadyInCloset

        # Log this redeem using the eventlogger.
        self.air.writeServerEvent('code-redeemed', avId = avId, limited = limited, issue = f'Code attempted to be redeemed: {code}')

        # Send our response.
        self.d_redeemCodeResult(avId, context, result, awardMgrResult)

    def getItemsForCode(self, code):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            # Invalid avatar id.
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'Could not parse the gender of an invalid avId')
            return

        av = self.air.doId2do.get(avId)

        if not av:
            # Invalid avatar.
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

        # Our codes.
        if code == 'gadzooks':
            shirt = CatalogClothingItem(1807, 0)
            return [shirt]

        if code in ('sillymeter', 'silly meter', 'silly-meter'):
            shirt = CatalogClothingItem(1753, 0)
            return [shirt]

        if code in ('gc-sbfo', 'gc sbfo', 'gcsbfo'):
            shirt = CatalogClothingItem(1788, 0)
            return [shirt]

        if code in ('getconnected', 'get connected', 'get_connected'):
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

        if code in ('sweet', 'tasty', 'beaned', 'party-fun'):
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

        if code == 'spooky-october':
            shirt = CatalogClothingItem(1001, 0)
            shorts = CatalogClothingItem(1746, 0)
            beans = CatalogBeanItem(12000, tagCode = 2)
            return [shirt, shorts, beans]

        if code == 'trunk':
            if av.getStyle().getGender() == 'm':
                trunk = CatalogFurnitureItem(4000, 0)
            else:
                shirt = CatalogFurnitureItem(4010, 0)
            return [trunk]

        if code == 'feeling-jolly':
            shirt = CatalogClothingItem(1100, 0)
            shorts = CatalogClothingItem(1104, 0)
            beans = CatalogBeanItem(12000, tagCode = 2)
            return [shirt, shorts, beans]

        return False

    def getCodeRedeemers(self, code):
        data = {
            'redeemCode': code,
            'secretKey': config.GetString('api-token'),
            'serverName': ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN]
        }

        request = requests.post('https://toontastic.sunrise.games/api/codes/getCodeRedeemers.php', data, headers = self.webHeaders).json()
        return json.loads(request['RedeemedBy'])

    def setRedeemedCode(self, code, avId):
        data = {
            'redeemCode': code,
            'secretKey': config.GetString('api-token'),
            'avatarId': avId,
            'serverName': ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN]
        }

        requests.post('https://toontastic.sunrise.games/api/codes/setCodeUsed.php', data, headers = self.webHeaders)
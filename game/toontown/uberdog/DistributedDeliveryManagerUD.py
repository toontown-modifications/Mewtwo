"""The Toontown Delivery Manager UD handles all the delivery across all districts."""

from game.toontown.toonbase import ToontownGlobals
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from game.toontown.catalog import CatalogItemList
from game.toontown.catalog import CatalogItem
from game.toontown.catalog import CatalogBeanItem
from .LRUlist import LRUlist

import time

from direct.directnotify.DirectNotifyGlobal import directNotify

notify = directNotify.newCategory('DeliveryManagerUD')


class AddGiftRequestFR:
    def __init__(self, distObj, replyToChannelId, avatarId, newGift, senderId, context, retcode):
        self.distObj = distObj
        self.air = self.distObj.air
        self.replyToChannelId = replyToChannelId
        self.avatarId = avatarId
        self.newGift = newGift
        self.senderId = senderId
        self.context = context
        self.retcode = retcode

        self.air.dbInterface.queryObject(self.air.dbId, avatarId, self.finish,
                                         self.air.dclassesByName['DistributedToonUD'],
                                         ('setGiftSchedule',))

    def finish(self, dclass, fields):
        giftBlob = self.distObj.avatarIdToGifts.getData(self.avatarId)
        if giftBlob is None:
            giftBlob = fields.get("setGiftSchedule")[0]
        giftItem = CatalogItemList.CatalogItemList(self.newGift, store = CatalogItem.Customization | CatalogItem.DeliveryDate)
        giftList = CatalogItemList.CatalogItemList(giftBlob, store = CatalogItem.Customization | CatalogItem.DeliveryDate)
        giftList.append(giftItem[0])
        giftBlob = giftList.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.distObj.writeGiftFR(self.avatarId, giftBlob, self.replyToChannelId, self.senderId, self.context, self.retcode)


class AddGift:
    def __init__(self, distObj, avatarId, newGift):
        self.distObj = distObj
        self.air = self.distObj.air
        self.avatarId = avatarId
        self.newGift = newGift
        self.air.dbInterface.queryObject(self.air.dbId, avatarId, self.finish,
                                         self.air.dclassesByName['DistributedToonUD'],
                                         ('setGiftSchedule',))

    def finish(self, dclass, fields):
        giftBlob = self.distObj.avatarIdToGifts.getData(self.avatarId)
        if giftBlob is None:
            giftBlob = fields.get("setGiftSchedule")[0]
        giftItem = CatalogItemList.CatalogItemList(self.newGift, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        giftList = CatalogItemList.CatalogItemList(giftBlob, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if giftItem[0].giftCode != ToontownGlobals.GIFT_RAT:
            notify.debug('Gift Item not RAT')
            giftList.append(giftItem[0])
            giftBlob = giftList.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)
        else:
            notify.debug('Gift Item is RAT')
            giftBlob = AccumRATBeans(giftItem[0], giftBlob)
        self.distObj.writeGift(self.avatarId, giftBlob)


def AccumRATBeans(newGift, GiftListBlob):
    giftList = CatalogItemList.CatalogItemList(GiftListBlob, store = CatalogItem.Customization | CatalogItem.DeliveryDate)
    found = 0

    if newGift.giftCode == ToontownGlobals.GIFT_RAT:
        numBeans = newGift.beanAmount
        for index in range(len(giftList)):
            if giftList[index].giftCode == ToontownGlobals.GIFT_RAT and found == 0:
                found = 1
                giftList[index].beanAmount = numBeans + giftList[index].beanAmount
    if found:
        notify.debug('RAT already on list')
        giftList.markDirty()
    else:
        notify.debug('RAT is not on the list')
        giftList.append(newGift)

    newBlobList = giftList.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)

    return newBlobList


class DeliverGiftRequest:
    def __init__(self, distObj, avatarId, time):
        self.distObj = distObj
        self.air = self.distObj.air
        self.avatarId = avatarId
        self.time = time
        self.air.dbInterface.queryObject(self.air.dbId, avatarId, self.finish,
                                         self.air.dclassesByName['DistributedToonUD'],
                                         ('setGiftSchedule',))

    def finish(self, dclass, fields):
        giftListBlob = fields.get("setGiftSchedule")[0]
        giftList = CatalogItemList.CatalogItemList(giftListBlob, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        delivered, remaining = giftList.extractDeliveryItems(self.time)
        giftBlob = remaining.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.distObj.writeGiftField(self.avatarId, giftBlob)


class PurchaseGiftRequest:
    def __init__(self, distObj, replyToChannelId, senderId, receiverId, itemBlob, context):
        notify.debug('PurchaseGiftRequest INIT')
        self.distObj = distObj
        self.air = self.distObj.air
        self.replyToChannelId = replyToChannelId
        self.senderId = senderId
        self.receiverId = receiverId
        self.itemBlob = itemBlob
        self.context = context
        self.retcode = None
        self.item = None
        self.catalogType = None
        self.cost = 0

        self.sender = None
        self.receiver = None

        self.air.generateObjectFromDatabase(senderId, self.__gotSender)
        self.air.generateObjectFromDatabase(receiverId, self.__gotReceiver)

    def __gotSender(self, sender):
        if sender is None:
            notify.warning('sender returned None!')
            return
        self.sender = sender
        if self.sender and self.receiver:
            self.finish()

    def __gotReceiver(self, receiver):
        if receiver is None:
            notify.warning('receiver returned None!')
            return
        self.receiver = receiver
        if self.sender and self.receiver:
            self.finish()

    def checkCatalog(self, retcode):
        if self.item in self.sender.monthlyCatalog:
            self.catalogType = CatalogItem.CatalogTypeMonthly
        elif self.item in self.sender.weeklyCatalog:
            self.catalogType = CatalogItem.CatalogTypeWeekly
        elif self.item in self.sender.backCatalog:
            self.catalogType = CatalogItem.CatalogTypeBackorder
        else:
            self.air.writeServerEvent('suspicious', self.sender.doId, 'purchaseItem %s not in catalog' % self.item)
            notify.warning("Avatar %s attempted to purchase %s, not on catalog." % (self.sender.doId, self.item))
            notify.warning("Avatar %s weekly: %s" % (self.sender.doId, self.sender.weeklyCatalog))
            return ToontownGlobals.P_NotInCatalog
        return retcode

    def checkMoney(self, retcode):
        price = self.item.getPrice(self.catalogType)
        self.cost = price
        if price > self.sender.getTotalMoney():
            self.air.writeServerEvent('suspicious', self.sender.doId, 'purchaseItem %s not enough money' % self.item)
            notify.warning("Avatar %s attempted to purchase %s, not enough money." % (self.sender.doId, self.item))
            return ToontownGlobals.P_NotEnoughMoney
        return retcode

    def checkGift(self, retcode):
        if self.item.isGift() <= 0:
            return ToontownGlobals.P_NotAGift
        return retcode

    def checkGender(self, retcode):
        if (self.item.forBoysOnly() and self.receiver.dna.getGender() == 'f') or (self.item.forGirlsOnly() and self.receiver.dna.getGender() == 'm'):
            return ToontownGlobals.P_WillNotFit
        return retcode

    def checkPurchaseLimit(self, retcode):
        if self.item.reachedPurchaseLimit(self.receiver):
            return ToontownGlobals.P_ReachedPurchaseLimit
        return retcode

    def checkMailbox(self, retcode):
        if len(self.receiver.mailboxContents) + len(self.receiver.onGiftOrder) >= ToontownGlobals.MaxMailboxContents:
            if len(self.receiver.mailboxContents) == 0:
                retcode = ToontownGlobals.P_OnOrderListFull
            else:
                retcode = ToontownGlobals.P_MailboxFull
        return retcode

    def finish(self):
        self.item = CatalogItem.getItem(self.itemBlob, store=CatalogItem.Customization)
        retcode = None
        retcode = self.checkGift(retcode)
        retcode = self.checkCatalog(retcode)
        retcode = self.checkGender(retcode)
        retcode = self.checkPurchaseLimit(retcode)
        retcode = self.checkMailbox(retcode)
        if retcode is not None:
            self.distObj.sendUpdateToChannel(self.replyToChannelId, 'receiveRejectPurchaseGift',
                                             [self.senderId, self.context, retcode, self.cost])
        else:
            now = int(time.time() / 60 + 0.5)
            deliveryTime = self.item.getDeliveryTime() / self.distObj.timeScale
            if deliveryTime < 2:
                deliveryTime = 2
            self.item.deliveryDate = int(now + deliveryTime)
            itemList = CatalogItemList.CatalogItemList([self.item])
            itemBlob = itemList.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
            retcode = ToontownGlobals.P_ItemOnOrder
            self.distObj.addGiftFR(self.receiverId, itemBlob, self.senderId, self.context, retcode, self.replyToChannelId)


class GiveItem:
    def __init__(self, distObj, receiverId, itemBlob):
        self.distObj = distObj
        self.air = self.distObj.air
        self.receiverId = receiverId
        self.itemBlob = itemBlob
        self.item = None
        self.catalogType = None
        self.item = CatalogItem.getItem(self.itemBlob, store=CatalogItem.Customization)

        now = int(time.time() / 60 + 0.5)
        deliveryTime = 2
        self.item.deliveryDate = int(now + deliveryTime)
        itemList = CatalogItemList.CatalogItemList([self.item])
        itemBlob = itemList.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.distObj.addGift(self.receiverId, itemBlob)


class DistributedDeliveryManagerUD(DistributedObjectGlobalUD):
    timeScale = simbase.config.GetFloat('catalog-time-scale', 1.0)

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.avatarIdToName = LRUlist(8192)  # {} cache for names from the database
        self.avatarIdToGifts = LRUlist(8192)  # {} cache for gifts from the database
        self.giftPendingCounter = 0

    def giveGiftItemToAvatar(self, itemBlob, receiverId):
        notify.debug('Adding Unchecked Gift Item')
        myGiveItem = GiveItem(self, receiverId, itemBlob)

    def giveRecruitAToonPayment(self, receiverId, amount=1):
        notify.debug('Adding RAT Bonus')
        ratItem = CatalogBeanItem.CatalogBeanItem(amount)
        ratItem.giftTag = 0
        ratItem.giftCode = ToontownGlobals.GIFT_RAT
        itemBlob = ratItem.getBlob(store=CatalogItem.Customization)
        myGiveItem = GiveItem(self, receiverId, itemBlob)

    def receiveRequestPurchaseGift(self, giftBlob, receiverId, senderId, context):
        # this is where the message gets sent back to, in this case it is the calling Client
        replyToChannelAI = self.air.getSenderReturnChannel()
        myPGR = PurchaseGiftRequest(self, replyToChannelAI, senderId, receiverId, giftBlob, context)

    def addGiftFR(self, doId, newGift, senderId, context, retcode, replyToChannelId):
        """
        Appends an existing gift list with the parameter newGift
        doId is the DO that you want to append newGift onto
        newGift the gift blob you want to add
        """
        # check to see if the gift is in our cache dictionary
        giftBlob = self.avatarIdToGifts.getData(doId)
        giftItem = CatalogItemList.CatalogItemList(newGift, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.air.writeServerEvent("Adding Gift", doId, "sender %s receiver %s gift %s" % (senderId, doId, giftItem[0].getName()))
        if giftBlob is None:
            # if not in our cache
            myAddGiftRequestFR = AddGiftRequestFR(self, replyToChannelId, doId, newGift, senderId, context, retcode)
        else:
            # else it's in our cache
            giftList = CatalogItemList.CatalogItemList(giftBlob, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
            giftItem = CatalogItemList.CatalogItemList(newGift, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
            giftList.append(giftItem[0])

            giftBlob = giftList.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)
            self.writeGiftFR(doId, giftBlob, replyToChannelId, senderId, context, retcode)

    def writeGiftFR(self, avatarId, newGift, replyToChannelId, senderId, context, retcode):
        """
        Writes the newly appended gift to the database
        doId is the DO that you want to append newGift onto
        newGift final appended blob to write to the database
        replyToChannelId is where the message gets sent back to, in this case it is the calling AI
        """
        self.avatarIdToGifts.putData(avatarId, newGift)  # update the cache
        # update the database
        self.air.sendUpdateToDoId("DistributedToon", "setGiftSchedule", avatarId, [newGift])
        # return an Accept message to the AI caller
        self.sendUpdateToChannel(replyToChannelId, "receiveAcceptPurchaseGift", [senderId, context, retcode])

    def addGift(self, doId, newGift):
        """
        Appends an existing gift list with the parameter newGift
        doId is the DO that you want to append newGift onto
        newGift the gift blob you want to add
        """
        # check to see if the gift is in our cache dictionary
        giftBlob = self.avatarIdToGifts.getData(doId)
        giftItem = CatalogItemList.CatalogItemList(newGift, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.air.writeServerEvent("Adding Server Gift", doId, "receiver %s gift %s" % (doId, giftItem[0].getName()))
        if giftBlob is None:
            # if not in our cache
            myAddGift = AddGift(self, doId, newGift)
        else:
            # else it's in our cache
            giftList = CatalogItemList.CatalogItemList(giftBlob, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
            giftItem = CatalogItemList.CatalogItemList(newGift, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
            if giftItem[0].giftCode != ToontownGlobals.GIFT_RAT:

                giftList.append(giftItem[0])
                giftBlob = giftList.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)
            else:
                giftBlob = AccumRATBeans(giftItem[0], giftBlob)
            self.writeGift(doId, giftBlob)

    def writeGift(self, avatarId, newGift):
        """
        Writes the newly appended gift to the database
        doId is the DO that you want to append newGift onto
        newGift final appended blob to write to the database
        """
        # update the cache
        self.avatarIdToGifts.putData(avatarId, newGift)
        # update the database
        self.air.sendUpdateToDoId("DistributedToon", "setGiftSchedule", avatarId, [newGift])

    def deliverGifts(self, avId, time):
        """A request to have a toon's gifts delivered to their mailbox
        this simply removes old gifts based on the time parameter"""
        giftListBlob = self.avatarIdToGifts.getData(avId)
        if giftListBlob is None:
            # if not in our cache
            myAddGiftRequest = DeliverGiftRequest(self, avId, time)
        else:
            giftList = CatalogItemList.CatalogItemList(giftListBlob, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
            delivered, remaining = giftList.extractDeliveryItems(time)
            giftBlob = remaining.getBlob(CatalogItem.Customization | CatalogItem.DeliveryDate)
            self.writeGiftField(avId, giftBlob)

        notify.debug('Delivering Gifts for avatar %d' % avId)

    def writeGiftField(self, avatarId, giftBlob):
        """
        Rewrites the gift field
        doId is the DO that you want to append newGift onto
        giftBlob final blob to write to the database
        replyToChannel is where the message gets sent back to, in this case it is the calling AI
        """
        self.avatarIdToGifts.putData(avatarId, giftBlob)  # update the cache
        self.air.sendUpdateToDoId("DistributedToon", "setGiftSchedule", avatarId, [giftBlob])
        # update the database

    def requestAck(self):
        replyToChannel = self.air.getSenderReturnChannel()
        self.sendUpdateToChannel(replyToChannel, "returnAck", [])
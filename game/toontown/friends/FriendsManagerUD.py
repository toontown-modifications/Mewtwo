from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.PyDatagram import *
from direct.fsm.FSM import FSM

import functools, json, time

class GetAvatarInfoOperation(FSM):

    def __init__(self, mgr, senderId, avId, callback):
        FSM.__init__(self, 'GetAvatarInfoOperation')
        self.mgr = mgr
        self.senderId = senderId
        self.avId = avId
        self.callback = callback
        self.isPet = False

    def start(self):
        self.demand('GetAvatarInfo')

    def enterGetAvatarInfo(self):
        self.mgr.air.air.dbInterface.queryObject(self.mgr.air.air.dbId, self.avId, self.__gotAvatarInfo)

    def __gotAvatarInfo(self, dclass, fields):
        if dclass not in (self.mgr.air.air.dclassesByName['DistributedToonUD'], self.mgr.air.air.dclassesByName['DistributedPetAI']):
            self.demand('Failure', 'Invalid dclass for avId %d' % self.avId)
            return

        self.isPet = dclass == self.mgr.air.air.dclassesByName['DistributedPetAI']
        self.fields = fields
        self.fields['avId'] = self.avId
        self.demand('Finished')

    def enterFinished(self):
        if not self.isPet:
            self.mgr.avBasicInfoCache[self.avId] = {'expire': time.time() + config.GetInt('friend-detail-cache-expire', 3600), 'avInfo': [self.avId, self.fields['setName'][0], self.fields['setDNAString'][0], self.fields['setPetId'][0]]}

        self.callback(success = True, avId = self.senderId, fields = self.fields, isPet = self.isPet)

    def enterFailure(self, reason):
        self.mgr.notify.warning(reason)
        self.callback(success = False, avId = None, fields = None, isPet = False)

class GetFriendsListOperation(FSM):

    def __init__(self, mgr, avId, callback):
        FSM.__init__(self, 'GetFriendsListOperation')

        self.mgr = mgr
        self.avId = avId
        self.callback = callback

        self.friendsDetails = []
        self.iterated = 0
        self.operations = {}
        self.onlineFriends = []

    def start(self):
        self.demand('GetFriendsList')

    def enterGetFriendsList(self):
        self.mgr.air.air.dbInterface.queryObject(self.mgr.air.air.dbId, self.avId, self.__gotFriendsList)

    def __gotFriendsList(self, dclass, fields):
        if self.state != 'GetFriendsList':
            self.demand('Failure', '__gotFriendsList called when looking for friends list, avId %d' % self.avId)
            return

        if dclass != self.mgr.air.air.dclassesByName['DistributedToonUD']:
            self.demand('Failure', 'Invalid dclass for avId %d' % self.avId)
            return

        self.friendsList = fields['setFriendsList'][0]
        self.demand('GetFriendDetails')

    def enterGetFriendDetails(self):
        if len(self.friendsList) <= 0:
            self.callback(success = False, avId = self.avId, friendsDetails = None, onlineFriends = None)
            return

        for friendId, trueFriend in self.friendsList:
            details = self.mgr.avBasicInfoCache.get(friendId)
            if details:
                expire = details.get('expire')
                avInfo = details.get('avInfo')
                if expire and avInfo:
                    if expire > time.time():
                        self.friendsDetails.append(avInfo)
                        self.iterated += 1
                        self.__testFinished()
                        continue
                    else:
                        del self.mgr.avBasicInfoCache[friendId]

            newOperation = GetAvatarInfoOperation(self.mgr, self.avId, friendId, self.__gotAvatarInfo)
            newOperation.start()
            self.operations[friendId] = newOperation

    def __gotAvatarInfo(self, success, avId, fields, isPet):
        if fields['avId'] in self.operations:
            del self.operations[fields['avId']]

        if not success:
            self.demand('Failure', '__gotAvatarInfo received unsuccessful callback, avId=%d' % self.avId)
            return

        if self.state != 'GetFriendDetails':
            self.demand('Failure', '__gotAvatarInfo while not looking for friends details, avId=%d' % self.avId)
            return

        if avId != self.avId:
            self.demand('Failure', '__gotAvatarInfo response for wrong requester. wrongId=%d, rightId=%d' % (self.avId, avId))
            return

        self.iterated += 1
        self.friendsDetails.append([fields['avId'], fields['setName'][0], fields['setDNAString'][0], fields['setPetId'][0]])
        self.__testFinished()

    def __testFinished(self):
        if self.iterated >= len(self.friendsList) and len(self.operations) == 0:
            self.demand('CheckFriendsOnline')

    def enterCheckFriendsOnline(self):
        self.iterated = 0
        for friendId, trueFriend in self.friendsList:
            self.mgr.air.air.getActivated(friendId, self.__gotActivatedResp)

    def __gotActivatedResp(self, avId, activated):
        self.iterated += 1

        if activated:
            self.onlineFriends.append(avId)

        if self.iterated == len(self.friendsList):
            self.demand('Finished')

    def enterFinished(self):
        self.callback(success = True, avId = self.avId, friendsDetails = self.friendsDetails, onlineFriends = self.onlineFriends)

    def enterFailure(self, reason):
        self.mgr.notify.warning(reason)
        self.callback(success = False, avId = self.avId, friendsDetails = None, onlineFriends = None)

class UpdateAvatarFieldOperation(FSM):

    def __init__(self, mgr, senderId, avId, callback):
        FSM.__init__(self, 'UpdateAvatarFieldOperation')

        self.mgr = mgr
        self.senderId = senderId
        self.avId = avId
        self.callback = callback

        self.field = None
        self.value = None

    def start(self, field, value):
        self.field = field
        self.value = value
        self.demand('GetAvatarOnline')

    def enterGetAvatarOnline(self):
        self.mgr.air.air.getActivated(self.avId, self.__avatarOnlineResp)

    def __avatarOnlineResp(self, avId, activated):
        if self.state != 'GetAvatarOnline':
            self.demand('Failure', 'Received __avatarOnlineResp while not in GetAvatarOnline state.')
            return

        self.online = activated
        self.demand('UpdateAvatarField')

    def enterUpdateAvatarField(self):
        if self.online:
            dg = self.mgr.air.air.dclassesByName['DistributedToonUD'].aiFormatUpdate(self.field, self.avId, self.avId, self.mgr.air.air.ourChannel, [self.value])
            self.mgr.air.air.send(dg)
        else:
            self.mgr.air.air.dbInterface.updateObject(self.mgr.air.air.dbId, self.avId, self.mgr.air.air.dclassesByName['DistributedToonUD'], {self.field: [self.value]})

        self.demand('Finished')

    def enterFinished(self):
        self.callback(success = True, avId = self.senderId, online = self.online)

    def enterFailure(self, reason):
        self.mgr.notify.warning(reason)
        self.callback(success = False)

class FriendsManagerUD:
    notify = directNotify.newCategory('FriendsManagerUD')

    def __init__(self, air):
        self.air = air

        self.operations = {}
        self.avBasicInfoCache = {}

    def deleteOperation(self, avId):
        operation = self.operations.get(avId)
        if not operation:
            self.notify.debug('%s tried to delete non-existent operation!' % avId)
            return

        if operation.state != 'Off':
            operation.demand('Off')

        del self.operations[avId]

    def getFriendsListRequest(self, avId):
        if not avId:
            return

        if avId in self.operations:
            return

        newOperation = GetFriendsListOperation(self, avId, self.__gotFriendsList)
        newOperation.start()
        self.operations[avId] = newOperation

    def __gotFriendsList(self, success, avId, friendsDetails, onlineFriends):
        self.deleteOperation(avId)

        clientChannel = self.air.air.GetPuppetConnectionChannel(avId)

        if not success:
            return

        resp = PyDatagram()

        resp.addUint16(11) # CLIENT_GET_FRIEND_LIST_RESP
        resp.addUint8(0)
        resp.addUint16(len(friendsDetails))

        for field in friendsDetails:
            resp.addUint32(field[0])
            resp.addString(field[1])
            resp.addString(field[2])
            resp.addUint32(field[3])

        # Send it.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.air.send(dg)

        if not onlineFriends:
            return

        datagram = PyDatagram()
        datagram.addUint16(53) # CLIENT_FRIEND_ONLINE

        for friendId in onlineFriends:
            datagram.addUint32(friendId)
        
        datagram.addUint8(1)
        datagram.addUint8(1)

         # Send it.
        dgTwo = PyDatagram()
        dgTwo.addServerHeader(clientChannel, self.air.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dgTwo.addString(datagram.getMessage())
        self.air.air.send(dgTwo)

        #for friendId in onlineFriends:
            #self.comingOnline(avId, friendId)

    def getAvatarDetails(self, avId):
        senderId = self.air.getAvatarIdFromSender()

        if not senderId:
            return

        if senderId in self.operations:
            return

        newOperation = GetAvatarInfoOperation(self, senderId, avId, self.__gotAvatarDetails)
        newOperation.start()
        self.operations[senderId] = newOperation

    def __gotAvatarDetails(self, success, avId, fields, isPet):
        self.deleteOperation(avId)
        if not success:
            return

        if isPet:
            details = [
                ['setTraitSeed', fields['setTraitSeed'][0]],
                ['setSafeZone', fields['setSafeZone'][0]],
                ['setLastSeenTimestamp', fields.get('setLastSeenTimestamp', [0])[0]],
                ['setHead', fields['setHead'][0]],
                ['setEars', fields['setEars'][0]],
                ['setNose', fields['setNose'][0]],
                ['setTail', fields['setTail'][0]],
                ['setBodyTexture', fields['setBodyTexture'][0]],
                ['setColor', fields['setColor'][0]],
                ['setColorScale', fields['setColorScale'][0]],
                ['setEyeColor', fields['setEyeColor'][0]],
                ['setGender', fields['setGender'][0]],
                ['setOwnerId', fields['setOwnerId'][0]],
                ['setPetName', fields['setPetName'][0]]
            ]
        else:
            details = [
                ['setName', fields['setName'][0]],
                ['setExperience', fields['setExperience'][0].encode('base64')],
                ['setTrackAccess', fields['setTrackAccess'][0]],
                ['setTrackBonusLevel', fields['setTrackBonusLevel'][0]],
                ['setInventory', fields['setInventory'][0].encode('base64')],
                ['setHp', fields['setHp'][0]],
                ['setMaxHp', fields['setMaxHp'][0]],
                ['setDefaultShard', fields['setDefaultShard'][0]],
                ['setLastHood', fields['setLastHood'][0]],
                ['setDNAString', fields['setDNAString'][0].encode('base64')],
                ['setMailboxContents', fields['setMailboxContents'][0].encode('base64')],
                ['setAwardMailboxContents', fields['setAwardMailboxContents'][0].encode('base64')],
                ['setGiftSchedule', fields['setGiftSchedule'][0].encode('base64')],
                ['setDeliverySchedule', fields['setDeliverySchedule'][0].encode('base64')],
                ['setAwardSchedule', fields['setAwardSchedule'][0].encode('base64')],
                ['setHat', fields['setHat'][0], fields['setHat'][1], fields['setHat'][2]],
                ['setGlasses', fields['setGlasses'][0], fields['setGlasses'][1], fields['setGlasses'][2]],
                ['setBackpack', fields['setBackpack'][0], fields['setBackpack'][1], fields['setBackpack'][2]],
                ['setShoes', fields['setShoes'][0], fields['setShoes'][1], fields['setShoes'][2]],
                ['setHatList', fields['setHatList'][0]],
                ['setGlassesList', fields['setGlassesList'][0]],
                ['setBackpackList', fields['setBackpackList'][0]],
                ['setShoesList', fields['setShoesList'][0]],
                ['setCustomMessages', fields['setCustomMessages'][0]],
                ['setEmoteAccess', fields['setEmoteAccess'][0]],
                ['setClothesTopsList', fields['setClothesTopsList'][0]],
                ['setClothesBottomsList', fields['setClothesBottomsList'][0]],
                ['setPetTrickPhrases', fields['setPetTrickPhrases'][0]]
            ]

        self.sendUpdateToAvatarId(avId, 'avatarDetailsResp', [fields['avId'], json.dumps(details)])

    def removeFriend(self, avId, friendId):
        if not avId:
            return

        if avId in self.operations:
            return

        newOperation = GetAvatarInfoOperation(self, avId, avId, functools.partial(self.__handleRemoveFriend, friendId = friendId))
        newOperation.start()
        self.operations[avId] = newOperation

    def __handleRemoveFriend(self, success, avId, fields, isPet, friendId = None, final = False):
        self.deleteOperation(avId)

        if not (success and friendId):
            return

        if fields['avId'] not in [avId, friendId]:
            self.notify.warning('__handleRemoveFriend received wrong Toon fields from DB, avId=%d' % avId)
            return

        friendsList = fields['setFriendsList'][0]
        searchId = avId if final else friendId
        for index, friend in enumerate(friendsList):
            if friend[0] == searchId:
                del friendsList[index]
                break

        newOperation = UpdateAvatarFieldOperation(self, avId, friendId if final else avId, functools.partial(self.__handleFriendRemoved, friendId = friendId, final = final))
        newOperation.start('setFriendsList', friendsList)
        self.operations[avId] = newOperation

    def __handleFriendRemoved(self, success, avId, online = False, friendId = None, final = False):
        self.deleteOperation(avId)

        if not (success and friendId):
            return

        if not final:
            newOperation = GetAvatarInfoOperation(self, avId, friendId, functools.partial(self.__handleRemoveFriend, friendId = friendId, final = True))
            newOperation.start()
            self.operations[avId] = newOperation

    def comingOnline(self, avId, friendId):
        self.air.air.getActivated(friendId, functools.partial(self.__comingOnlineFriendOnline, otherId = avId))

    def __comingOnlineFriendOnline(self, avId, activated, otherId = None):
        clientChannel = self.air.air.GetPuppetConnectionChannel(avId)

        if not (otherId and activated):
            return

        # Declare our avatar to their friend.
        dg = PyDatagram()
        dg.addServerHeader(self.air.air.GetPuppetConnectionChannel(avId), self.air.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
        dg.addUint32(otherId)
        dg.addUint16(self.air.air.dclassesByName['DistributedToonUD'].getNumber())
        self.air.air.send(dg)

        # Declare their friend to our avatar.
        dg = PyDatagram()
        dg.addServerHeader(self.air.air.GetPuppetConnectionChannel(otherId), self.air.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
        dg.addUint32(avId)
        dg.addUint16(self.air.air.dclassesByName['DistributedToonUD'].getNumber())
        self.air.air.send(dg)

        # Tell the client that their friend is online.
        datagram = PyDatagram()
        datagram.addUint16(53) # CLIENT_FRIEND_ONLINE
        datagram.addUint32(otherId)
 
        datagram.addUint8(1)
        datagram.addUint8(1)

         # Send it.
        dgTwo = PyDatagram()
        dgTwo.addServerHeader(clientChannel, self.air.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dgTwo.addString(datagram.getMessage())
        self.air.air.send(dgTwo)

    def goingOffline(self, avId):
        newOperation = GetAvatarInfoOperation(self, avId, avId, self.__handleGoingOffline)
        newOperation.start()

    def __handleGoingOffline(self, success, avId, fields, isPet):
        if not success:
            return

        for friendId, trueFriend in fields['setFriendsList'][0]:
            self.air.air.getActivated(friendId, functools.partial(self.__handleGoneOffline, otherId = avId, accId = fields['setDISLid'][0]))

    def __handleGoneOffline(self, avId, activated, otherId = None, accId = None):
        clientChannel = self.air.air.GetPuppetConnectionChannel(avId)

        if not (otherId and activated and accId):
            return

        # Undeclare to the friend.
        dg = PyDatagram()
        dg.addServerHeader(self.air.air.GetPuppetConnectionChannel(avId), self.air.air.ourChannel, CLIENTAGENT_UNDECLARE_OBJECT)
        dg.addUint32(otherId)
        self.air.air.send(dg)

        # Undeclare to the now-offline avId.
        dg = PyDatagram()
        dg.addServerHeader(self.air.air.GetAccountConnectionChannel(accId), self.air.air.ourChannel, CLIENTAGENT_UNDECLARE_OBJECT)
        dg.addUint32(avId)
        self.air.air.send(dg)

        # Tell them they're offline.
        datagram = PyDatagram()
        datagram.addUint16(54) # CLIENT_FRIEND_OFFLINE
        datagram.addUint32(otherId)

         # Send it.
        dgTwo = PyDatagram()
        dgTwo.addServerHeader(clientChannel, self.air.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dgTwo.addString(datagram.getMessage())
        self.air.air.send(dgTwo)

    def clearList(self, avId):
        newOperation = GetAvatarInfoOperation(self, avId, avId, self.__handleClearListGotFriendsList)
        newOperation.start()
        self.operations[avId] = newOperation

    def __handleClearListGotFriendsList(self, success, avId, fields, isPet):
        if not success:
            return

        if avId != fields['avId']:
            return

        friendIds = fields['setFriendsList'][0][:]
        friendIds.append((avId, 1))
        if friendIds[0][0] == avId:
            return

        newOperation = GetAvatarInfoOperation(self, avId, friendIds[0][0], functools.partial(self.__handleClearListGotFriendData, friendIds = friendIds[1:]))
        newOperation.start()
        self.operations[avId] = newOperation

    def __handleClearListGotFriendData(self, success, avId, fields, isPet, friendIds = []):
        self.deleteOperation(avId)

        if not success:
            if friendIds:
                newOperation = GetAvatarInfoOperation(self, avId, friendIds[0][0], functools.partial(self.__handleClearListGotFriendData, friendIds = friendIds[1:]))
                newOperation.start()
                self.operations[avId] = newOperation
            else:
                return

        friendsIds = fields['setFriendsList'][0][:]
        if avId == fields['avId']:
            friendsIds = []
        else:
            for friend in friendsIds:
                if friend[0] == avId:
                    friendsIds.remove(friend)

        newOperation = UpdateAvatarFieldOperation(self, avId, fields['avId'], functools.partial(self.__handleClearListUpdatedAvatarField, friendId = fields['avId'], friendIds = friendIds[1:]))
        newOperation.start('setFriendsList', friendsIds)
        self.operations[avId] = newOperation

    def __handleClearListUpdatedAvatarField(self, success, avId, online = False, friendId = None, friendIds = []):
        self.deleteOperation(avId)

        if success and online:
            dg = self.air.dclassesByName['DistributedToonUD'].aiFormatUpdate('friendsNotify', friendId, friendId, self.air.ourChannel, [avId, 1])
            self.air.send(dg)

        if not friendIds:
            return

        newOperation = GetAvatarInfoOperation(self, avId, friendIds[0][0], functools.partial(self.__handleClearListGotFriendData, friendIds = friendIds[1:]))
        newOperation.start()
        self.operations[avId] = newOperation
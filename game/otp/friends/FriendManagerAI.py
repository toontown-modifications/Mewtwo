from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.MsgTypes import CLIENTAGENT_DECLARE_OBJECT

from game.otp.otpbase import OTPGlobals

import datetime, json, os, random, string, sys

class FriendManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('FriendManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.currentContext = 0

        self.requests = {}
        self.rngSeed = None

        self.filename = simbase.config.GetString('secret-friend-storage')
        self.secretFriendCodes = self.loadSecretFriendCodes()

        taskMgr.add(self.__secretFriendCodesTask, 'sf-codes-clear-task')

    def friendQuery(self, inviteeId):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            return

        if inviteeId not in self.air.doId2do:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to friend a player that does not exist!')
            return

        context = self.currentContext
        self.requests[context] = [[avId, inviteeId], 'friendQuery']
        self.currentContext += 1
        self.sendUpdateToAvatarId(inviteeId, 'inviteeFriendQuery', [avId, av.getName(), av.getDNAString(), context])

    def cancelFriendQuery(self, context):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        if context not in self.requests:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to cancel a request that doesn\'t exist!')
            return

        if avId != self.requests[context][0][0]:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to cancel someone else\'s request!')
            return

        self.requests[context][1] = 'cancelled'
        self.sendUpdateToAvatarId(self.requests[context][0][1], 'inviteeCancelFriendQuery', [context])

    def inviteeFriendConsidering(self, yesNo, context):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        if context not in self.requests:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to consider a friend request that doesn\'t exist!')
            return

        if avId != self.requests[context][0][1]:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to consider for someone else!')
            return

        if self.requests[context][1] != 'friendQuery':
            self.air.writeServerEvent('suspicious', avId, 'Player tried to reconsider friend request!')
            return

        if yesNo != 1:
            self.sendUpdateToAvatarId(self.requests[context][0][0], 'friendConsidering', [yesNo, context])
            del self.requests[context]
            return

        self.requests[context][1] = 'friendConsidering'
        self.sendUpdateToAvatarId(self.requests[context][0][0], 'friendConsidering', [yesNo, context])

    def inviteeFriendResponse(self, response, context):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        if context not in self.requests:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to respond to a friend request that doesn\'t exist!')
            return

        if avId != self.requests[context][0][1]:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to respond to someone else\'s request!')
            return

        if self.requests[context][1] == 'cancelled':
            self.air.writeServerEvent('suspicious', avId, 'Player tried to respond to a non-active friend request!')
            return

        self.sendUpdateToAvatarId(self.requests[context][0][0], 'friendResponse', [response, context])

        if response == 1:
            requestedAv = self.air.doId2do.get(self.requests[context][0][1])

            if not requestedAv:
                del self.requests[context]
                return

            requesterAv = self.air.doId2do.get(self.requests[context][0][0])
            if not requesterAv:
                del self.requests[context]
                return

            dg = PyDatagram()
            dg.addServerHeader(self.GetPuppetConnectionChannel(requestedAv.getDoId()), self.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
            dg.addUint32(requesterAv.getDoId())
            dg.addUint16(self.air.dclassesByName['DistributedToonAI'].getNumber())
            self.air.send(dg)

            dg = PyDatagram()
            dg.addServerHeader(self.GetPuppetConnectionChannel(requesterAv.getDoId()), self.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
            dg.addUint32(requestedAv.getDoId())
            dg.addUint16(self.air.dclassesByName['DistributedToonAI'].getNumber())
            self.air.send(dg)

            # Route this to the "UD" Friends manager.
            self.air.netMessenger.send('postAddFriend', [requesterAv.getDoId(), requestedAv.getDoId()])
            self.air.netMessenger.send('postAddFriend', [requestedAv.getDoId(), requesterAv.getDoId()])

            requestedAv.extendFriendsList(requesterAv.getDoId(), 0)
            requesterAv.extendFriendsList(requestedAv.getDoId(), 0)

            requestedAv.d_setFriendsList(requestedAv.getFriendsList())
            requesterAv.d_setFriendsList(requesterAv.getFriendsList())

        del self.requests[context]

    def inviteeAcknowledgeCancel(self, context):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            return

        if context not in self.requests:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to acknowledge the cancel of a friend request that doesn\'t exist!')
            return

        if avId != self.requests[context][0][1]:
            self.air.writeServerEvent('suspicious', avId, 'Player tried to acknowledge someone else\'s cancel!')
            return

        if self.requests[context][1] != 'cancelled':
            self.air.writeServerEvent('suspicious', avId, 'Player tried to cancel non-cancelled request!')
            return

        del self.requests[context]

    def requestSecret(self):
        if not self.rngSeed:
            self.rngSeed = random.randrange(sys.maxsize)

        random.seed(self.rngSeed)

        def id_generator(size=3, chars=string.ascii_lowercase + string.digits):
            return "".join(random.Random().choice(chars) for _ in range(size))

        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            return

        if len(av.getFriendsList()) >= OTPGlobals.MaxFriends:
            self.d_requestSecretResponse(avId, 0, '')
        else:
            day = datetime.datetime.now().day
            secret = f"{id_generator(3)} {id_generator(3)}"
            self.secretFriendCodes[secret] = (avId, day)

            # This is a cheeky way to shuffle the seed.
            # We don't want SF code repeats, So we reseed each time to prevent them.
            self.rngSeed += avId
            random.seed(self.rngSeed)

            self.updateSecretFriendCodesFile()
            self.d_requestSecretResponse(avId, 1, secret)
            self.air.writeServerEvent('secret-code-requested', avId=avId, secret=secret)

    def d_requestSecretResponse(self, avId, result, secret):
        if not avId:
            return

        self.sendUpdateToAvatarId(avId, 'requestSecretResponse', [result, secret])

    def submitSecret(self, secret):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            return

        secretInfo = self.secretFriendCodes.get(secret)

        if not secretInfo:
            self.d_submitSecretResponse(avId, 0, 0)
            return

        friendId = secretInfo[0]
        friend = self.air.doId2do.get(friendId)

        if av:
            if friend:
                if avId == friendId:
                    self.d_submitSecretResponse(avId, 3, 0)
                    self.removeSecret(secret)
                elif len(friend.getFriendsList()) >= OTPGlobals.MaxFriends or len(
                        av.getFriendsList()) >= OTPGlobals.MaxFriends:
                    self.d_submitSecretResponse(avId, 2, friendId)
                else:
                    dg = PyDatagram()
                    dg.addServerHeader(self.GetPuppetConnectionChannel(friendId), self.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
                    dg.addUint32(avId)
                    dg.addUint16(self.air.dclassesByName['DistributedToonAI'].getNumber())
                    self.air.send(dg)

                    dg = PyDatagram()
                    dg.addServerHeader(self.GetPuppetConnectionChannel(avId), self.air.ourChannel, CLIENTAGENT_DECLARE_OBJECT)
                    dg.addUint32(friendId)
                    dg.addUint16(self.air.dclassesByName['DistributedToonAI'].getNumber())
                    self.air.send(dg)

                    # Route this to the "UD" Friends manager.
                    self.air.netMessenger.send('postAddFriend', [avId, friendId])
                    self.air.netMessenger.send('postAddFriend', [friendId, avId])

                    friend.extendFriendsList(avId, 1)
                    av.extendFriendsList(friendId, 1)

                    friend.d_setFriendsList(friend.getFriendsList())
                    av.d_setFriendsList(av.getFriendsList())

                    self.d_submitSecretResponse(avId, 1, friendId)
                    self.removeSecret(secret)
            else:
                # Friend is offline!
                def handleAvatar(dclass, fields):
                    if dclass != self.air.dclassesByName['DistributedToonAI']:
                        return

                    newFriendsList = []
                    oldFriendsList = fields['setFriendsList'][0]

                    if len(oldFriendsList) >= OTPGlobals.MaxFriends:
                        self.d_submitSecretResponse(avId, 2, friendId)
                        return

                    for oldFriend in oldFriendsList:
                        newFriendsList.append(oldFriend)

                    newFriendsList.append((avId, 1))
                    self.air.dbInterface.updateObject(self.air.dbId, friendId, self.air.dclassesByName['DistributedToonAI'], {'setFriendsList': [newFriendsList]})
                    av.extendFriendsList(friendId, 1)
                    av.d_setFriendsList(av.getFriendsList())
                    self.d_submitSecretResponse(avId, 1, friendId)
                    self.removeSecret(secret)

                self.air.dbInterface.queryObject(self.air.dbId, friendId, handleAvatar)

        self.air.writeServerEvent('secret-code-submitted', avId=avId, friendId=friendId, secret=secret)

    def d_submitSecretResponse(self, avId, result, friendId):
        if not avId:
            return

        self.sendUpdateToAvatarId(avId, 'submitSecretResponse', [result, friendId])

    def removeSecret(self, secret):
        if secret in self.secretFriendCodes:
            del self.secretFriendCodes[secret]
            self.updateSecretFriendCodesFile()

    def loadSecretFriendCodes(self):
        try:
            secretCodesFile = open(self.filename, 'r')
            secretCodesData = json.load(secretCodesFile)
            return secretCodesData
        except:
            return {}

    def updateSecretFriendCodesFile(self):
        try:
            if not os.path.exists(os.path.dirname(self.filename)):
                os.makedirs(os.path.dirname(self.filename))

            secretCodesFile = open(self.filename, 'w')
            secretCodesFile.seek(0)
            json.dump(self.secretFriendCodes, secretCodesFile)
            secretCodesFile.close()
        except:
            import traceback
            traceback.print_exc()

    def __secretFriendCodesTask(self, task):
        for secret in list(self.secretFriendCodes.keys()):
            secretCodeInfo = self.secretFriendCodes[secret]
            secretCodeDay = secretCodeInfo[1]
            today = datetime.datetime.now().day
            if secretCodeDay + 2 == today:
                self.notify.info(f'Removing 2-day-old Secret Friend code: {secret}')
                self.removeSecret(secret)

        return task.again
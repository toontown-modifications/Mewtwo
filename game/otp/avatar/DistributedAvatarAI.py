from game.otp.ai.AIBaseGlobal import *
from game.otp.otpbase import OTPGlobals
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.distributed import DistributedNodeAI
from direct.task import Task
from game.toontown.chat.TTWhiteList import TTWhiteList

class DistributedAvatarAI(DistributedNodeAI.DistributedNodeAI):

    def __init__(self, air):
        DistributedNodeAI.DistributedNodeAI.__init__(self, air)
        self.hp = 0
        self.maxHp = 0

        self.whiteList = TTWhiteList()
        
    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)

    def d_setName(self, name):
        self.sendUpdate('setName', [name])

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def b_setMaxHp(self, maxHp):
        self.d_setMaxHp(maxHp)
        self.setMaxHp(maxHp)

    def d_setMaxHp(self, maxHp):
        self.sendUpdate('setMaxHp', [maxHp])

    def setMaxHp(self, maxHp):
        self.maxHp = maxHp

    def getMaxHp(self):
        return self.maxHp

    def b_setHp(self, hp):
        self.d_setHp(hp)
        self.setHp(hp)

    def d_setHp(self, hp):
        self.sendUpdate('setHp', [hp])

    def setHp(self, hp):
        self.hp = hp

    def getHp(self):
        return self.hp

    def b_setLocationName(self, locationName):
        self.d_setLocationName(locationName)
        self.setLocationName(locationName)

    def d_setLocationName(self, locationName):
        pass

    def setLocationName(self, locationName):
        self.locationName = locationName

    def getLocationName(self):
        return self.locationName

    def b_setActivity(self, activity):
        self.d_setActivity(activity)
        self.setActivity(activity)

    def d_setActivity(self, activity):
        pass

    def setActivity(self, activity):
        self.activity = activity

    def getActivity(self):
        return self.activity

    def toonUp(self, num):
        if self.hp >= self.maxHp:
            return
        self.hp = min(self.hp + num, self.maxHp)
        self.b_setHp(self.hp)

    def getRadius(self):
        return OTPGlobals.AvatarDefaultRadius

    def checkAvOnShard(self, avId):
        senderId = self.air.getAvatarIdFromSender()
        onShard = False
        if simbase.air.doId2do.get(avId):
            onShard = True
        self.sendUpdateToAvatarId(senderId, 'confirmAvOnShard', [avId, onShard])

    def setParentStr(self, parentToken):
        if parentToken:
            senderId = self.air.getAvatarIdFromSender()
            self.air.writeServerEvent('Admin chat warning', senderId, 'using setParentStr to send "%s"' % parentToken)
            self.notify.warning('Admin chat warning: %s using setParentStr to send "%s"' % (senderId, parentToken))
        DistributedNodeAI.DistributedNodeAI.setParentStr(self, parentToken)

    def setTalk(self, todo, todo2, todo3, message, modifications, todo4):
        sender = self.air.getAvatarIdFromSender()

        if not sender:
            return

        filteredMessage, modifications = self.filterWhiteList(message)

        dclass = self.air.dclassesByName['DistributedAvatarAI']
        datagram = dclass.aiFormatUpdate('setTalk', sender, sender, self.air.ourChannel, [0, 0, '', filteredMessage, modifications, 0])
        self.air.send(datagram)

    def filterWhiteList(self, message):
        modifications = []
        words = message.split(' ')
        offset = 0


        for word in words:
            if word and not self.whiteList.isWord(word):
                modifications.append((offset, offset + len(word) - 1))

            offset += len(word) + 1

        filteredMessage = message

        for modStart, modStop in modifications:
            filteredMessage = filteredMessage[:modStart] + '*' * (modStop - modStart + 1) + filteredMessage[modStop + 1:]

        return filteredMessage, modifications
    
    def setTalkWhisper(self, receiverAvId, todo2, todo3, message, modifications, todo4):
        sender = self.air.getAvatarIdFromSender()

        if not sender:
            return

        cleanMessage, modifications = self.filterWhiteList(message)

        dclass = self.air.dclassesByName['DistributedAvatarAI']

        if not receiverAvId:
            datagram = dclass.aiFormatUpdate('setTalkWhisper', receiverAvId, receiverAvId, self.air.ourChannel, [sender, sender, '', cleanMessage, modifications, 0])
        else:
            datagram = dclass.aiFormatUpdate('setTalkWhisper', receiverAvId, receiverAvId, self.air.ourChannel, [sender, sender, '', cleanMessage, modifications, 0])

        self.air.send(datagram)
    
    def setTalkAccount(self, receiverAvId, todo2, todo3, message, modifications, todo4):
        sender = self.air.getAvatarIdFromSender()
        print(sender)

        if not sender:
            return

        dclass = self.air.dclassesByName['DistributedAvatarAI']
        datagram = dclass.aiFormatUpdate('setTalkAccount', receiverAvId, receiverAvId, self.air.ourChannel, [sender, sender, '', message, [], 0])
        self.air.send(datagram)

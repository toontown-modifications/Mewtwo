from panda3d.core import UniqueIdAllocator

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD

from game.toontown.parties import PartyGlobals
from game.toontown.parties.PartyInfo import PartyInfoAI

import datetime

class DistributedPartyManagerUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory('DistributedPartyManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)

        self.host2party = {}
        self.publicParties = {}
        self.partyDoIds = set()

        self.wantInstantParties = config.GetBool('want-instant-parties', True)
        self.inviteKeyAllocator = UniqueIdAllocator(1, 65535)

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)

        self.__startPartiesTask()

    def delete(self):
        taskMgr.remove(self.uniqueName('parties-task'))

        DistributedObjectGlobalUD.delete(self)

    def sendUpdateToAV(self, avId, field, args = []):
        dg = self.air.dclassesByName['DistributedToonUD'].getFieldByName(field).aiFormatUpdate(avId, avId,
                                                                                               simbase.air.ourChannel,
                                                                                               args)
        self.air.send(dg)

    def __startPartiesTask(self):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        delay = (60 - now.second) + 60 * (4 - (now.minute % 5))
        taskMgr.doMethodLater(delay, self.__partiesTask, self.uniqueName('parties-task'))

    def __partiesTask(self, task):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        for party in self.host2party.values():
            partyInfo = party[1]
            partyStruct = party[2]
            partyId = partyInfo.partyId
            hostId = partyInfo.hostId
            if self.canStartParty(partyInfo) and partyInfo.status == PartyGlobals.PartyStatus.Pending:
                partyInfo.status = PartyGlobals.PartyStatus.CanStart
                self.sendUpdateToAV(hostId, 'setHostedParties', [[partyStruct]])
                self.sendUpdateToAV(hostId, 'setPartyCanStart', [partyId])
            elif self.isTooLate(partyInfo):
                partyInfo.status = PartyGlobals.PartyStatus.NeverStarted
                self.sendUpdateToAV(hostId, 'setHostedParties', [[partyStruct]])

        task.delayTime = (60 - now.second) + 60 * (4 - (now.minute % 5))
        return task.again

    def canStartParty(self, partyInfo):
        return self.wantInstantParties or partyInfo.startTime < datetime.datetime.now(
            tz=self.air.toontownTimeManager.serverTimeZone)

    def isTooLate(self, partyInfo):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        delta = datetime.timedelta(minutes=15)
        endStartable = partyInfo.startTime + delta
        return endStartable > now

    def addParty(self, hostId, partyDoId, startTime, endTime, isPrivate, inviteTheme, activities, decorations,
                 inviteeIds, cost):
        partyTimeFormat = '%Y-%m-%d %H:%M:%S'
        startDate = datetime.datetime.strptime(startTime, partyTimeFormat)
        endDate = datetime.datetime.strptime(endTime, partyTimeFormat)
        party = self.host2party[hostId][1]
        self.host2party[hostId][4] = self.inviteKeyAllocator.allocate()
        if party:
            self.sendUpdateToAI(partyDoId, 'addPartyResponseUdToAi',
                                [self.host2party[hostId][0], PartyGlobals.AddPartyErrorCode.TooManyHostedParties,
                                 self.host2party[hostId][4]])
            return

        partyInfo = PartyInfoAI(self.host2party[hostId][0], hostId, startDate.year, startDate.month, startDate.day,
                                startDate.hour, startDate.minute, endDate.year, endDate.month, endDate.day,
                                endDate.hour, endDate.minute, isPrivate, inviteTheme, activities, decorations,
                                PartyGlobals.PartyStatus.Pending)

        partyStruct = [
            self.host2party[hostId][0],
            hostId,
            startDate.year,
            startDate.month,
            startDate.day,
            startDate.hour,
            startDate.minute,
            endDate.year,
            endDate.month,
            endDate.day,
            endDate.hour,
            endDate.minute,
            isPrivate,
            inviteTheme,
            activities,
            decorations,
            PartyGlobals.PartyStatus.Pending
        ]

        self.host2party[hostId][1] = partyInfo
        self.host2party[hostId][2] = partyStruct
        self.host2party[hostId][3] = inviteeIds

        self.sendUpdateToAI(partyDoId, 'addPartyResponseUdToAi',
                            [self.host2party[hostId][0], PartyGlobals.AddPartyErrorCode.AllOk,
                             self.host2party[hostId][4]])

        if self.wantInstantParties:
            taskMgr.remove(self.uniqueName('parties-task'))
            taskMgr.doMethodLater(15, self.__partiesTask, self.uniqueName('parties-task'))

    def markInviteAsReadButNotReplied(self, todo0, todo1):
        pass

    def respondToInvite(self, partyDoId, avId, inviteKey, partyId, response):
        inviteeIds = []
        for partyIndices in self.host2party.values():
            if partyIndices[0] == partyId:
                inviteeIds = partyIndices[3]
                break

        if not inviteeIds:
            return

        if avId not in inviteeIds:
            return

        self.sendUpdateToAI(partyDoId, 'respondToInviteResponse',
                            [avId, inviteKey, partyId, response, 0])

    def changePrivateRequest(self, todo0, todo1):
        pass

    def changePrivateRequestAiToUd(self, hostId, partyId, newPrivateStatus):
        party = self.host2party.get(hostId)
        partyStruct = party[2]

        if party is None:
            self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyStruct[1] != hostId:
            self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyStruct[16] not in (PartyGlobals.PartyStatus.CanStart, PartyGlobals.PartyStatus.Pending):
            self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.AlreadyStarted)
            return

        partyStruct[12] = newPrivateStatus
        self.host2party[hostId] = party

        if partyId in self.publicParties.keys():
            publicPartyInfo = self.publicParties[partyId]
            minLeft = int((PartyGlobals.PARTY_DURATION - (datetime.datetime.now() - publicPartyInfo['started']).seconds) / 60)
            self.updateToPublicPartyInfoUdToAllAi(publicPartyInfo['shardId'], publicPartyInfo['zoneId'], partyId,
                                                  hostId, publicPartyInfo['numberOfGuests'],
                                                  publicPartyInfo['hostName'], partyStruct[14], minLeft,
                                                  partyStruct[12])

        self.sendUpdateToAV(hostId, 'setHostedParties', [[partyStruct]])
        self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                         PartyGlobals.ChangePartyFieldErrorCode.AllOk)

    def changePrivateResponseUdToAi(self, hostId, partyId, newPrivateStatus, errorCode):
        partyDoId = self.air.getMsgSender()
        self.sendUpdateToAI(partyDoId, 'changePrivateResponseUdToAi', [hostId, partyId, newPrivateStatus, errorCode])

    def changePrivateResponse(self, todo0, todo1, todo2):
        pass

    def changePartyStatusRequest(self, partyId, newPartyStatus):
        pass

    def changePartyStatusRequestAiToUd(self, hostId, partyId, newPartyStatus):
        party = self.host2party.get(hostId)
        partyStruct = party[2]

        if party is None:
            self.changePrivateResponseUdToAi(hostId, partyId, newPartyStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyStruct[1] != hostId:
            self.changePrivateResponseUdToAi(hostId, partyId, newPartyStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyStruct[16] not in (PartyGlobals.PartyStatus.CanStart, PartyGlobals.PartyStatus.Pending):
            self.changePrivateResponseUdToAi(hostId, partyId, newPartyStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.AlreadyStarted)
            return

        partyStruct[16] = newPartyStatus
        self.sendUpdateToAV(hostId, 'setHostedParties', [[partyStruct]])

        beansRefunded = 0
        if newPartyStatus == PartyGlobals.PartyStatus.Cancelled:
            beansRefunded = PartyGlobals.getCostOfParty(party[1]) * PartyGlobals.PartyRefundPercentage
            if hostId in self.host2party:
                del self.host2party[hostId]
        else:
            self.host2party[hostId] = party
            self.updateToPublicPartyInfoUdToAllAi(0, 0, 0, 0, 0, 0, 0, 0, 0)

        self.changePartyStatusResponseUdToAi(partyId, newPartyStatus, PartyGlobals.ChangePartyFieldErrorCode.AllOk,
                                             beansRefunded)
        if newPartyStatus == PartyGlobals.PartyStatus.Cancelled:
            self.partyHasFinishedUdToAllAi(partyId)

    def changePartyStatusResponseUdToAi(self, partyId, newPartyStatus, errorCode, beansRefunded):
        partyDoId = self.air.getMsgSender()
        self.sendUpdateToAI(partyDoId, 'changePartyStatusResponseUdToAi', [partyId, newPartyStatus, errorCode, beansRefunded])

    def changePartyStatusResponse(self, todo0, todo1, todo2, todo3):
        pass

    def partyInfoOfHostRequestAiToUd(self, partyDoId, hostId):
        if hostId in self.host2party:
            partyInfo = self.host2party[hostId][1]
            if partyInfo.status == PartyGlobals.PartyStatus.CanStart:
                partyStruct = self.host2party[hostId][2]
                inviteeIds = self.host2party[hostId][3]
                self.sendUpdateToAI(partyDoId, 'partyInfoOfHostResponseUdToAi', [partyStruct, inviteeIds])
                return

        partyId = self.host2party[hostId][1].partyId
        party = self.publicParties[partyId]
        zoneId = party['zoneId']

        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(avId, 'receivePartyZone', [hostId, partyId, zoneId])

    def partyInfoOfHostFailedResponseUdToAi(self, todo0):
        pass

    def givePartyRefundResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def freeZoneIdFromPlannedParty(self, avId, zoneId):
        pass

    def sendAvToPlayground(self, todo0, todo1):
        pass

    def exitParty(self, zoneIdOfAv):
        pass

    def removeGuest(self, ownerId, avId):
        pass

    def partyManagerAIStartingUp(self, todo0, todo1):
        pass

    def partyManagerAIGoingDown(self, todo0, todo1):
        pass

    def partyHasStartedAiToUd(self, partyId, shardId, zoneId, hostId, hostName):
        self.publicParties[partyId] = {
            'shardId': shardId,
            'zoneId': zoneId,
            'hostId': hostId,
            'numberOfGuests': 0,
            'hostName': hostName,
            'started': datetime.datetime.now()}

        party = self.host2party.get(hostId)
        partyStruct = party[2]
        minLeft = int((PartyGlobals.PARTY_DURATION - (datetime.datetime.now() - self.publicParties[partyId]['started']).seconds) / 60)
        self.updateToPublicPartyInfoUdToAllAi(shardId, zoneId, partyId, hostId, 0, hostName, partyStruct[14], minLeft,
                                              partyStruct[12])
        party[1].status = PartyGlobals.PartyStatus.Started

    def toonHasEnteredPartyAiToUd(self, avId, partyId, gateId):
        if partyId not in self.publicParties:
            return

        party = self.publicParties[partyId]
        if party['numberOfGuests'] >= PartyGlobals.MaxToonsAtAParty:
            return

        party['numberOfGuests'] += 1
        shardId = party['shardId']
        zoneId = party['zoneId']
        hostId = party['hostId']
        hostName = party['hostName']
        minLeft = int((PartyGlobals.PARTY_DURATION - (datetime.datetime.now() - party['started']).seconds) / 60)
        partyStruct = self.host2party.get(hostId)[2]
        self.updateToPublicPartyInfoUdToAllAi(shardId, zoneId, partyId, hostId, 0, hostName, partyStruct[14], minLeft,
                                              partyStruct[12])

        actIds = []
        for activity in partyStruct[14]:
            actIds.append(activity[0])
        partyInfoTuple = [party['shardId'], party['zoneId'], party['numberOfGuests'], party['hostName'], actIds, 0]

        self.toonHasEnteredPartyUdToAI(avId, gateId, partyInfoTuple)

    def toonHasEnteredPartyUdToAI(self, avId, gateId, partyInfoTuple):
        partyDoId = self.air.getMsgSender()

        self.sendUpdateToAI(partyDoId, 'toonHasEnteredPartyUdToAI', [avId, gateId, partyInfoTuple])

    def toonHasExitedPartyAiToUd(self, todo0):
        pass

    def partyHasFinishedUdToAllAi(self, partyId):
        self.sendUpdateToAllAI('partyHasFinishedUdToAllAi', [partyId])

    def updateToPublicPartyInfoUdToAllAi(self, shardId, zoneId, partyId, hostId, numberOfGuests, hostName, activityIds,
                                         minLeft, isPrivate):
        actIds = []
        for activity in activityIds:
            actIds.append(activity[0])
        self.sendUpdateToAllAI('updateToPublicPartyInfoUdToAllAi', [hostId, partyId, shardId, zoneId, numberOfGuests,
                                                                    isPrivate, hostName, actIds, minLeft])
    def updateToPublicPartyCountUdToAllAi(self, todo0, todo1):
        pass

    def requestShardIdZoneIdForHostId(self, hostId):
        partyId = self.host2party[hostId][1].partyId
        party = self.publicParties[partyId]
        shardId = party['shardId']
        zoneId = party['zoneId']
        self.sendShardIdZoneIdToAvatar(shardId, zoneId)

    def sendShardIdZoneIdToAvatar(self, shardId, zoneId):
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar', [shardId, zoneId])

    def partyManagerUdStartingUp(self):
        pass

    def updateAllPartyInfoToUd(self, hostId, partyId, todo2, todo3, todo4, todo5, todo6, todo7, todo8):
        if hostId not in self.host2party:
            sender = self.air.getMsgSender()
            self.partyDoIds.add(sender)
            self.host2party[hostId] = [partyId, None, None, None, None]

    def forceCheckStart(self):
        pass

    def requestMw(self, todo0, todo1, todo2, todo3):
        pass

    def mwResponseUdToAllAi(self, todo0, todo1, todo2, todo3):
        pass

    def sendUpdateToAI(self, doId, field, args = []):
        dg = self.dclass.aiFormatUpdate(field, doId, doId, self.doId, args)
        self.air.send(dg)

    def sendUpdateToAllAI(self, field, args = []):
        for partyDoId in self.partyDoIds:
            self.sendUpdateToAI(partyDoId, field, args)

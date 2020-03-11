from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify.DirectNotifyGlobal import directNotify

from game.otp.distributed.OtpDoGlobals import *

from game.toontown.parties import PartyGlobals
from game.toontown.parties.DistributedPartyAI import DistributedPartyAI
from game.toontown.parties.InviteInfo import InviteInfoBase
from game.toontown.parties.PartyInfo import PartyInfoAI

import datetime, time

class DistributedPartyManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedPartyManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.host2party = {}
        self.party2host = {}
        self.publicParties = {}
        self.avId2context = {}

    def addPartyRequest(self, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, inviteeIds):
        senderId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(hostId)

        if not av:
            self.air.writeServerEvent('suspicious', avId=senderId,
                                      issue='Toon tried to create a party but does not exist on the server!')
            return
        if hostId != senderId:
            self.air.writeServerEvent('suspicious', avId=senderId,
                                      issue='Toon tried to create a party as someone else!')
            return

        startDate = datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
        endDate = datetime.datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S')
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
        self.party2host[self.host2party[hostId][0]][1] = partyInfo
        cost = PartyGlobals.getCostOfParty(partyInfo)
        av.takeMoney(cost)
        self.sendUpdateToUD('updateAllPartyInfoToUd', [hostId, self.host2party[hostId][0], 0, 0, 0, 0, '', [], 0])
        self.sendUpdateToUD('addParty',
                            [hostId, self.doId, startTime, endTime, isPrivate, inviteTheme, activities,
                             decorations, inviteeIds, cost])

    def addPartyResponseUdToAi(self, partyId, errorCode, inviteKey):
        hostId = self.party2host[partyId][0]
        partyStruct = self.host2party[hostId][2]
        self.host2party[hostId][6] = inviteKey
        self.sendUpdateToAvatarId(hostId, 'addPartyResponse', [hostId, errorCode])
        inviteInfo = InviteInfoBase(inviteKey, self.host2party[hostId][0], PartyGlobals.InviteStatus.NotRead)
        inviteInfoStruct = [inviteInfo.inviteKey, inviteInfo.partyId, inviteInfo.status]
        host = self.air.doId2do.get(hostId)
        if host:
            host.sendUpdate('setHostedParties', [[partyStruct]])
            inviteeIds = self.host2party[hostId][3]
            for inviteeId in inviteeIds:
                invitee = self.air.doId2do.get(inviteeId)
                if not invitee:
                    continue

                invites = invitee.invites[:]
                if inviteInfoStruct not in invites:
                    invites.append(inviteInfoStruct)

                invitee.setInvites(invites)
                invitee.sendUpdate('setInvites', [invites])

                partiesInvitedTo = invitee.partiesInvitedTo[:]
                if partyStruct not in partiesInvitedTo:
                    partiesInvitedTo.append(partyStruct)

                invitee.setPartiesInvitedTo(partiesInvitedTo)
                invitee.sendUpdate('setPartiesInvitedTo', [partiesInvitedTo])

    def markInviteAsReadButNotReplied(self, todo0, todo1):
        pass

    def respondToInviteResponse(self, avId, inviteKey, partyId, response, todo4):
        if not avId:
            return

        context = self.avId2context.get(avId)
        if not context:
            return

    def changePrivateRequest(self, partyId, newPrivateStatus):
        hostId = self.air.getAvatarIdFromSender()
        self.changePrivateRequestAiToUd(hostId, partyId, newPrivateStatus)

    def changePrivateRequestAiToUd(self, hostId, partyId, newPrivateStatus):
        self.sendUpdateToUD('changePrivateRequestAiToUd', [hostId, partyId, newPrivateStatus])

    def changePrivateResponseUdToAi(self, hostId, partyId, newPrivateStatus, errorCode):
        self.changePrivateResponse(hostId, partyId, newPrivateStatus, errorCode)

    def changePrivateResponse(self, hostId, partyId, newPrivateStatus, errorCode):
        av = self.air.doId2do.get(hostId)
        if not av:
            return

        self.sendUpdateToAvatarId(hostId, 'changePrivateResponse', [partyId, newPrivateStatus, errorCode])

    def changePartyStatusRequest(self, partyId, newPartyStatus):
        hostId = self.air.getAvatarIdFromSender()
        self.changePartyStatusRequestAiToUd(hostId, partyId, newPartyStatus)

    def changePartyStatusRequestAiToUd(self, hostId, partyId, newPartyStatus):
        self.sendUpdateToUD('changePartyStatusRequestAiToUd', [hostId, partyId, newPartyStatus])

    def changePartyStatusResponseUdToAi(self, partyId, newPartyStatus, errorCode, beansRefunded):
        self.changePartyStatusResponse(partyId, newPartyStatus, errorCode, beansRefunded)

    def changePartyStatusResponse(self, partyId, newPartyStatus, errorCode, beansRefunded):
        hostId = self.party2host[partyId][0]

        av = self.air.doId2do.get(hostId)
        if not av:
            return

        av.addMoney(beansRefunded)
        self.sendUpdateToAvatarId(hostId, 'changePartyStatusResponse', [partyId, newPartyStatus, errorCode,
                                                                        beansRefunded])

    def partyInfoOfHostFailedResponseUdToAi(self, todo0):
        pass

    def partyInfoOfHostResponseUdToAi(self, partyStruct, inviteeIds):
        hostId = partyStruct[1]
        host = self.air.doId2do.get(hostId)
        if not host:
            return

        self.host2party[hostId][2] = partyStruct
        self.host2party[hostId][3] = inviteeIds

        zoneId, partyId = self.createParty(hostId, partyStruct)

        self.sendUpdateToAvatarId(hostId, 'receivePartyZone', [hostId, partyId, zoneId])

    def givePartyRefundResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def getPartyZone(self, avId, zoneId, planningParty):
        senderId = self.air.getAvatarIdFromSender()
        if planningParty:
            partyId = self.air.allocateChannel()
            self.host2party[avId] = [partyId, None, None, None, None, None, None]
            self.party2host[partyId] = [avId, None]
            self.sendUpdateToAvatarId(senderId, 'receivePartyZone', [avId, partyId, zoneId])
        else:
            self.sendUpdateToUD('partyInfoOfHostRequestAiToUd', [self.doId, avId])

    def freeZoneIdFromPlannedParty(self, todo0, todo1):
        pass

    def sendAvToPlayground(self, todo0, todo1):
        pass

    def exitParty(self, todo0):
        pass

    def removeGuest(self, ownerId, avId):
        pass

    def partyManagerAIStartingUp(self, todo0, todo1):
        pass

    def partyManagerAIGoingDown(self, todo0, todo1):
        pass

    def partyHasStartedAiToUd(self, partyId, shardId, zoneId, hostId, hostName):
        self.sendUpdateToUD('partyHasStartedAiToUd', [partyId, shardId, zoneId, hostId, hostName])

    def toonHasEnteredPartyAiToUd(self, avId, partyId, gateId):
        self.sendUpdateToUD('toonHasEnteredPartyAiToUd', [avId, partyId, gateId])

    def toonHasEnteredPartyUdToAI(self, avId, gateId, partyInfoTuple):
        gate = self.air.doId2do.get(gateId)

        if not gate:
            return

        gate.setParty(avId, partyInfoTuple)

    def toonHasExitedPartyAiToUd(self, todo0):
        pass

    def partyHasFinishedUdToAllAi(self, partyId):
        if partyId in self.party2host:
            del self.party2host[partyId]
        for hostId in [hostId for hostId in self.host2party.keys() if self.host2party[hostId] == partyId]:
            del self.host2party[hostId]

    def updateToPublicPartyInfoUdToAllAi(self, hostId, partyId, shardId, zoneId, numberOfGuests, isPrivate, hostName,
                                         activityIds, minLeft):
        self.publicParties[partyId] = {
            'shardId': shardId,
            'zoneId': zoneId,
            'hostId': hostId,
            'numberOfGuests': numberOfGuests,
            'hostName': hostName,
            'activityIds': activityIds,
            'minLeft': minLeft,
            'started': datetime.datetime.now(),
            'isPrivate': isPrivate}

    def updateToPublicPartyCountUdToAllAi(self, todo0, todo1):
        pass

    def requestShardIdZoneIdForHostId(self, hostId):
        self.sendUpdateToUD('requestShardIdZoneIdForHostId', [hostId])

    def sendShardIdZoneIdToAvatar(self, shardId, zoneId):
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar', [shardId, zoneId])

    def partyManagerUdStartingUp(self):
        pass

    def forceCheckStart(self):
        pass

    def requestMw(self, todo0, todo1, todo2, todo3):
        pass

    def mwResponseUdToAllAi(self, todo0, todo1, todo2, todo3):
        pass

    def canBuyParties(self):
        return True

    def getPublicParties(self):
        publicPartiesList = []
        for partyId in self.publicParties:
            party = self.publicParties[partyId]
            if party['isPrivate']:
                continue
            minLeft = int((PartyGlobals.PARTY_DURATION - (datetime.datetime.now() - party['started']).seconds) / 60)
            if minLeft <= 0:
                #self.closeParty(partyId)
                continue
            guests = max(0, min(party.get('numGuests', 0), 255))
            publicPartiesList.append([party['shardId'], party['zoneId'], guests, party.get('hostName', ''),
                                      party.get('activities', []), minLeft])

        return publicPartiesList

    def createParty(self, hostId, partyStruct):
        host = self.air.doId2do.get(hostId)
        if not host:
            return

        zoneId = self.air.allocateZone()
        self.host2party[hostId][4] = zoneId

        partyId = partyStruct[0]

        party = DistributedPartyAI(self.air, hostId, zoneId, self.host2party[hostId][1])
        for activity in party.partyInfo.activityList:
            if activity.activityId == PartyGlobals.ActivityIds.PartyClock:
                party.setPartyClockInfo(activity.x, activity.y, activity.h)

        party.setInviteeIds(self.host2party[hostId][3])
        party.setPartyState(False)
        party.setPartyInfoTuple(tuple(partyStruct))
        party.setPartyStartedTime(time.strftime('%Y-%m-%d %H:%M:%S'))
        party.setHostName(host.getName())
        party.generateWithRequiredAndId(partyId, self.air.districtId, zoneId)
        self.host2party[hostId][5] = party

        self.partyHasStartedAiToUd(partyId, self.air.ourChannel, zoneId, hostId, host.getName())

        return zoneId, partyId

    def getPartyIdFromInviteKey(self, inviteKey):
        for partyIndices in self.host2party.values():
            if partyIndices[6] == inviteKey:
                return partyIndices[0]

    def d_respondToInvite(self, avId, response, context, inviteKey):
        partyId = self.getPartyIdFromInviteKey(inviteKey)
        if not partyId:
            return

        if avId in self.avId2context.keys():
            return

        self.avId2context[avId] = context

        self.sendUpdateToUD('respondToInvite', [self.doId, avId, inviteKey, partyId, response])

    def sendUpdateToUD(self, field, args = []):
        dg = self.dclass.aiFormatUpdate(field, OTP_DO_ID_TOONTOWN_PARTY_MANAGER, OTP_DO_ID_TOONTOWN_PARTY_MANAGER,
                                        self.doId, args)
        self.air.send(dg)

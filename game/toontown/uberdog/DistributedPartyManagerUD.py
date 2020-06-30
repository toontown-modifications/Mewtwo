import datetime
import os
from pickle import dump, load

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectUD import DistributedObjectUD
from panda3d.core import UniqueIdAllocator

from game.toontown.parties.PartyGlobals import ChangePartyFieldErrorCode, getCostOfParty, PartyStatus
from game.toontown.parties.PartyGlobals import InviteStatus
from game.toontown.parties.PartyInfo import PartyInfoAI

class DistributedPartyManagerUD(DistributedObjectUD):
    notify = directNotify.newCategory('DistributedPartyManagerUD')

    def __init__(self, air):
        DistributedObjectUD.__init__(self, air)

        self.partyDoIds = set()
        self.hostId2partyInfo = {}
        self.partyId2invites = {}
        self.avId2invites = {}
        self.avId2partiesInvitedTo = {}
        self.avId2partyReplies = {}
        self.avId2inviteKey = {}
        self.partyId2inviteeIds = {}
        self.inviteKeyAllocator = UniqueIdAllocator(0, 65535)

    def announceGenerate(self):
        DistributedObjectUD.announceGenerate(self)

        # Register our channel so that we can receive field updates from AIs.
        self.air.registerForChannel(self.doId)

        # Create the Parties backup folder if it doesn't exist already.
        backupPath = 'backups/parties/'

        if not os.path.exists(backupPath):
            os.makedirs(backupPath)

        # Load our dicts.
        self.load()

        # Set up our scheduling task.
        self.runSchedulingTask()

    def delete(self):
        taskMgr.remove(self.uniqueName('check-start-parties'))
        DistributedObjectUD.delete(self)

    def load(self):
        fileName = os.path.join('backups/parties/', 'party-manager.wackyfuntime')
        if not os.path.exists(fileName):
            return

        with open(fileName, 'rb') as f:
            partyData = load(f)

        if not partyData:
            # Don't load anything I guess something something fuck you?
            return

        self.partyDoIds = partyData['partyDoIds']
        self.hostId2partyInfo = partyData['hostId2partyInfo']
        self.partyId2invites = partyData['partyId2invites']
        self.avId2invites = partyData['avId2invites']
        self.avId2partiesInvitedTo = partyData['avId2partiesInvitedTo']
        self.avId2partyReplies = partyData['avId2partyReplies']
        self.avId2inviteKey = partyData['avId2inviteKey']
        self.partyId2inviteeIds = partyData['partyId2inviteeIds']

        self.notify.info('Successfully loaded party data from file')

    def save(self):
        # Save all our dicts to a file.
        fileName = os.path.join('backups/parties/', 'party-manager.wackyfuntime')

        partyData = {}
        partyData['partyDoIds'] = self.partyDoIds
        partyData['hostId2partyInfo'] = self.hostId2partyInfo
        partyData['partyId2invites'] = self.partyId2invites
        partyData['avId2invites'] = self.avId2invites
        partyData['avId2partiesInvitedTo'] = self.avId2partiesInvitedTo
        partyData['avId2partyReplies'] = self.avId2partyReplies
        partyData['avId2inviteKey'] = self.avId2inviteKey
        partyData['partyId2inviteeIds'] = self.partyId2inviteeIds

        with open(fileName, 'wb+') as f:
            dump(partyData, f)

    def getSchedulingDelay(self):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)

        # The delay in this case is the amount of seconds until we reach the next 5 minutes.
        delay = (60 - now.second) + 60 * (4 - (now.minute % 5))

        return delay

    def runSchedulingTask(self):
        delay = self.getSchedulingDelay()
        taskMgr.doMethodLater(delay, self.__checkStartParties, self.uniqueName('check-start-parties'))

    def __checkStartParties(self, task):
        for partyInfo in list(self.hostId2partyInfo.values()):
            hostId = partyInfo.hostId
            if self.isTooLate(partyInfo):
                partyInfo.status = PartyStatus.NeverStarted
                partyInfoTuple = self.getPartyInfoTuple(partyInfo)
                self.annihilateParty(hostId, partyInfo.partyId)
                self.sendUpdateToAvatar(hostId, 'setHostedParties', [[partyInfoTuple]])
            elif self.canStartParty(partyInfo) and partyInfo.status == PartyStatus.Pending:
                # Start the party now.
                partyInfo.status = PartyStatus.CanStart
                partyInfoTuple = self.getPartyInfoTuple(partyInfo)
                self.sendUpdateToAvatar(hostId, 'setHostedParties', [[partyInfoTuple]])
                self.sendUpdateToAvatar(hostId, 'setPartyCanStart', [partyInfo.partyId])

        task.delayTime = self.getSchedulingDelay()
        return task.again

    def canStartParty(self, partyInfo):
        if config.GetBool('want-instant-parties', True):
            return True

        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        return partyInfo.startTime < now

    def isTooLate(self, partyInfo):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        delta = datetime.timedelta(minutes=15)
        tooLate = partyInfo.startTime + delta
        return now > tooLate

    def getPartyInfoTuple(self, partyInfo):
        partyInfoTuple = (
            partyInfo.partyId,
            partyInfo.hostId,
            partyInfo.startTime.year,
            partyInfo.startTime.month,
            partyInfo.startTime.day,
            partyInfo.startTime.hour,
            partyInfo.startTime.minute,
            partyInfo.endTime.year,
            partyInfo.endTime.month,
            partyInfo.endTime.day,
            partyInfo.endTime.hour,
            partyInfo.endTime.minute,
            partyInfo.isPrivate,
            partyInfo.inviteTheme,
            partyInfo.activityList,
            partyInfo.decors,
            partyInfo.status
        )
        return partyInfoTuple

    def addParty(self, hostId, partyId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, inviteeIds,
                 zoneId):
        # Get the shitty ID of the fucking AI.
        doId = self.air.getMsgSender()

        # Get our time variables:
        PARTY_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        startDateTime = datetime.datetime.strptime(startTime, PARTY_TIME_FORMAT)
        startYear = startDateTime.year
        startMonth = startDateTime.month
        startDay = startDateTime.day
        startHour = startDateTime.hour
        startMinute = startDateTime.minute
        endDateTime = datetime.datetime.strptime(endTime, PARTY_TIME_FORMAT)
        endYear = endDateTime.year
        endMonth = endDateTime.month
        endDay = endDateTime.day
        endHour = endDateTime.hour
        endMinute = endDateTime.minute

        # Create our PartyInfo.
        partyInfo = PartyInfoAI(partyId, hostId, startYear, startMonth, startDay, startHour,
                                startMinute, endYear, endMonth, endDay, endHour, endMinute,
                                isPrivate, inviteTheme, activities, decorations, PartyStatus.Pending)

        # Add the information to our dict.
        self.hostId2partyInfo[hostId] = partyInfo

        # add the inviteeIds to partyId2inviteeIds because bernie can still win
        self.partyId2inviteeIds[partyId] = inviteeIds

        # Calculate the cost of the party so that the AI can deduct USD.
        cost = getCostOfParty(partyInfo)

        # Tell the shitty AI.
        self.sendUpdateToAI(doId, 'addPartyResponseUdToAi', [partyId, PartyStatus.Pending, cost])

        # invite shit BWEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
        partyInfoTuple = self.getPartyInfoTuple(partyInfo)
        partyReplies = []
        partyReplyInfoBases = []
        for inviteeId in inviteeIds:
            partyReply = [inviteeId, InviteStatus.NotRead]
            partyReplies.append(partyReply)

            inviteKey = self.inviteKeyAllocator.allocate()
            self.avId2inviteKey[inviteeId] = inviteKey
            newInvite = [inviteKey, partyId, InviteStatus.NotRead, hostId]
            invites = self.partyId2invites.get(partyId, [])
            if newInvite not in invites:
                invites.append(newInvite)

            self.partyId2invites[partyId] = invites[:]

            avId2invites = self.avId2invites.get(inviteeId, [])
            if newInvite[0:3] not in avId2invites:
                avId2invites.append(newInvite[0:3])

            self.avId2invites[inviteeId] = avId2invites[:]

            partiesInvitedTo = self.avId2partiesInvitedTo.get(inviteeId, [])
            if partyInfoTuple not in partiesInvitedTo:
                partiesInvitedTo.append(partyInfoTuple)

            self.avId2partiesInvitedTo[inviteeId] = partiesInvitedTo[:]

            # we need to send the goddamn fucking invites to the invitees.
            # both the invites and the parties invited to because fuck you.
            self.sendUpdateToAvatar(inviteeId, 'setInvites', [avId2invites])
            self.sendUpdateToAvatar(inviteeId, 'setPartiesInvitedTo', [partiesInvitedTo])

        partyReplyInfoBase = [partyId, partyReplies]
        partyReplyInfoBases.append(partyReplyInfoBase)
        self.avId2partyReplies[hostId] = partyReplyInfoBases

        self.sendUpdateToAvatar(hostId, 'setHostedParties', [[partyInfoTuple]])
        self.sendUpdateToAvatar(hostId, 'setPartyReplies', [partyReplyInfoBases])

        # Save.
        self.save()

    def addPartyResponse(self, todo0, todo1):
        pass

    def addPartyResponseUdToAi(self, todo0, todo1, todo2):
        pass

    def markInviteAsReadButNotReplied(self, senderId, inviteKey):
        ourInvite = None
        for invite in list(self.partyId2invites.values()):
            if invite[0][0] == inviteKey:
                ourInvite = invite[:]
                break

        ourInvite[0][2] = InviteStatus.ReadButNotReplied
        self.partyId2invites[ourInvite[0][1]] = ourInvite[:]

        ourAvId = None
        ourAvIdInvite = None
        for avId, inviteTuple in self.avId2invites.items():
            if inviteTuple[0][0] == inviteKey:
                ourAvId = avId
                ourAvIdInvite = inviteTuple[:]
                break

        ourAvIdInvite[0][2] = InviteStatus.ReadButNotReplied
        self.avId2invites[ourAvId] = ourAvIdInvite[:]

        self.sendUpdateToAvatar(ourInvite[0][3], 'updateReply',
                                [ourInvite[0][1], senderId, InviteStatus.ReadButNotReplied])

        self.save()

    def respondToInvite(self, senderId, todo1, todo2, inviteKey, status):
        partyId = None
        senderInvites = self.avId2invites.get(senderId)
        if not senderInvites:
            return

        for senderInvite in senderInvites:
            if senderInvite[0] == inviteKey:
                partyId = senderInvite[1]
                senderInvite[2] = status

        self.avId2invites[senderId] = senderInvites[:]

        if not partyId:
            return

        invites = self.partyId2invites.get(partyId)
        if not invites:
            return

        hostId = None
        for invite in invites:
            if invite[0] == inviteKey:
                hostId = invite[3]
                invite[2] = status

        self.partyId2invites[partyId] = invites[:]

        if not hostId:
            return

        self.sendUpdateToAvatar(hostId, 'updateReply', [partyId, senderId, status])
        self.save()

    def respondToInviteResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def changePrivateRequestAiToUd(self, hostId, partyId, privateStatus):
        doId = self.air.getMsgSender()

        if hostId not in self.hostId2partyInfo:
            # AI is sending us garbage.
            return

        # Change the actual party status.
        self.hostId2partyInfo[hostId].isPrivate = privateStatus

        self.sendUpdateToAI(doId, 'changePrivateResponseUdToAi', [
            hostId,
            partyId,
            privateStatus,
            ChangePartyFieldErrorCode.AllOk])

        self.save()

    def changePartyStatusRequestAiToUd(self, hostId, partyId, partyStatus):
        doId = self.air.getMsgSender()

        if hostId not in self.hostId2partyInfo:
            # AI is sending us garbage.
            return

        # Change the actual party status.
        self.hostId2partyInfo[hostId].status = partyStatus

        if partyStatus == PartyStatus.Cancelled:
            # Kill the party.
            self.annihilateParty(hostId, partyId)

        self.sendUpdateToAI(doId, 'changePartyStatusResponseUdToAi', [
            hostId,
            partyId,
            partyStatus,
            ChangePartyFieldErrorCode.AllOk])

        self.save()

    def partyInfoOfHostRequestAiToUd(self, hostId, avId):
        # Get the shard ID.
        doId = self.air.getMsgSender()

        # Check to make sure the AI is requesting for information that exists.
        if hostId not in self.hostId2partyInfo:
            # We don't have information for this host ID...
            self.sendUpdateToAI(doId, 'partyInfoOfHostFailedResponseUdToAi', [avId])
            return

        # Send the data to the AI.
        self.sendUpdateToAI(doId, 'partyInfoOfHostResponseUdToAi',
                            [self.getPartyInfoTuple(self.hostId2partyInfo[hostId]), [avId, hostId]])

        self.hostId2partyInfo[hostId].status = PartyStatus.Started
        self.save()

        partyInfo = self.hostId2partyInfo.get(hostId)
        if not partyInfo:
            return

        partyId = partyInfo.partyId
        inviteeIds = self.partyId2inviteeIds.get(partyId)
        if not inviteeIds:
            return

        for inviteeId in inviteeIds:
            self.sendUpdateToAvatar(inviteeId, 'setPartyStatus', [partyId, self.hostId2partyInfo[hostId].status])

    def givePartyRefundResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def freeZoneIdFromPlannedParty(self, todo0, todo1):
        pass

    def sendAvToPlayground(self, todo0, todo1):
        pass

    def exitParty(self, todo0):
        pass

    def removeGuest(self, todo0, todo1):
        pass

    def partyManagerAIStartingUp(self, shardId, doId):
        self.partyDoIds.add(doId)

    def partyManagerAIGoingDown(self, todo0, todo1):
        pass

    def partyHasStartedAiToUd(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def toonHasEnteredPartyAiToUd(self, todo0):
        pass

    def toonHasExitedPartyAiToUd(self, todo0):
        pass

    def partyHasFinishedUdToAllAi(self, todo0):
        pass

    def updateToPublicPartyInfoUdToAllAi(self, todo0, todo1, todo2, todo3, todo4, todo5, todo6, todo7, todo8):
        pass

    def updateToPublicPartyCountUdToAllAi(self, todo0, todo1):
        pass

    def requestShardIdZoneIdForHostId(self, todo0):
        pass

    def sendShardIdZoneIdToAvatar(self, todo0, todo1):
        pass

    def partyManagerUdStartingUp(self):
        pass

    def updateAllPartyInfoToUd(self, hostId, partyId, zoneId, minLeft, status, numberOfGuests, hostName, activityIds,
                               shardId):
        if not minLeft:
            # Kill the party.
            self.annihilateParty(hostId, partyId)
            return

        self.sendUpdateToAllAI('updateToPublicPartyInfoUdToAllAi',
                               [hostId, partyId, zoneId, minLeft, status, numberOfGuests, hostName, activityIds,
                                shardId])

    def annihilateParty(self, hostId, partyId):
        # We don't want to update the public party info, rather we want to delete
        # our own information of this party and tell every AI to delete theirs.
        # First, remove the party from our own dicts.
        if hostId in self.hostId2partyInfo:
            del self.hostId2partyInfo[hostId]
        if partyId in self.partyId2invites:
            del self.partyId2invites[partyId]
        if partyId in self.partyId2inviteeIds:
            del self.partyId2inviteeIds[partyId]

        # Tell each AI to delete this party from their dict(s).
        self.sendUpdateToAllAI('partyHasFinishedUdToAllAi', [hostId])

        # Finally, save.
        self.save()

    def forceCheckStart(self):
        pass

    def requestMw(self, todo0, todo1, todo2, todo3):
        pass

    def mwResponseUdToAllAi(self, todo0, todo1, todo2, todo3):
        pass

    def sendUpdateToAI(self, doId, field, args=[]):
        dg = self.dclass.aiFormatUpdate(field, doId, doId, self.doId, args)
        self.air.send(dg)

    def sendUpdateToAllAI(self, field, args=[]):
        for partyDoId in self.partyDoIds:
            self.sendUpdateToAI(partyDoId, field, args)

    def sendUpdateToAvatar(self, avId, field, args=[]):
        dg = self.air.dclassesByName['DistributedToonUD'].getFieldByName(field).aiFormatUpdate(avId, avId,
                                                                                               simbase.air.ourChannel,
                                                                                               args)
        self.air.send(dg)

    def avatarOnline(self, avId):
        partyInfo = self.hostId2partyInfo.get(avId)
        if partyInfo:
            partyInfoTuple = self.getPartyInfoTuple(partyInfo)
            self.sendUpdateToAvatar(avId, 'setHostedParties', [[partyInfoTuple]])
            if partyInfo.status == PartyStatus.CanStart:
                self.sendUpdateToAvatar(avId, 'setPartyCanStart', [partyInfo.partyId])

        avId2invites = self.avId2invites.get(avId)
        if avId2invites:
            self.sendUpdateToAvatar(avId, 'setInvites', [avId2invites])

        partiesInvitedTo = self.avId2partiesInvitedTo.get(avId)
        if partiesInvitedTo:
            self.sendUpdateToAvatar(avId, 'setPartiesInvitedTo', [partiesInvitedTo])

        partyReplies = self.avId2partyReplies.get(avId)
        if partyReplies:
            self.sendUpdateToAvatar(avId, 'setPartyReplies', [partyReplies])

        if partyInfo:
            invites = self.partyId2invites.get(partyInfo.partyId)
            inviteeIds = self.partyId2inviteeIds.get(partyInfo.partyId)
            for inviteeId in inviteeIds:
                inviteKey = self.avId2inviteKey.get(inviteeId, -1)
                if inviteKey < 0:
                    continue

                for invite in invites:
                    if invite[0] == inviteKey:
                        self.sendUpdateToAvatar(avId, 'updateReply', [partyInfo.partyId, inviteeId, invite[2]])

        partyIds = []
        for partyId, inviteeIds in self.partyId2inviteeIds.items():
            for inviteeId in inviteeIds:
                if inviteeId == avId:
                    partyIds.append(partyId)
                    break

        parties = []
        for partyId in partyIds:
            for partyInfo in list(self.hostId2partyInfo.values()):
                if partyInfo.partyId == partyId:
                    parties.append(partyInfo)
                    break

        for party in parties:
            taskMgr.doMethodLater(5,
                                  lambda x: self.sendUpdateToAvatar(avId, 'setPartyStatus',
                                                                    [party.partyId, party.status]),
                                  self.uniqueName('set-party-status-%s' % avId), appendTask=False)

import datetime
import os
import time
from pickle import dump, load

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.otp.distributed.OtpDoGlobals import OTP_DO_ID_TOONTOWN_PARTY_MANAGER
from game.toontown.parties.DistributedPartyAI import DistributedPartyAI
from game.toontown.parties.PartyGlobals import ActivityIds, DefaultPartyDuration, PartyStatus
from game.toontown.parties.PartyGlobals import GoToPartyStatus, AddPartyErrorCode, PartyRefundPercentage
from game.toontown.parties.PartyInfo import PartyInfoAI

class DistributedPartyManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedPartyManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        # Structure of this dict:
        # {partyId: [hostId, shardId, zoneId, minLeft, status, numberOfGuests, hostName, activityIds]}
        self.partyInfo = {}

        self.hostId2data = {}
        self.partyId2hostId = {}
        self.partyId2partyCost = {}
        self.hostId2zoneId = {}
        self.hostId2publicParty = {}
        self.hostId2partyInfo = {}
        self.zoneId2hostId = {}
        self.hostId2hostName = {}
        self.hostId2startedTime = {}
        self.partyId2partyGuests = {}

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

        # Register our channel so that the UD can send us updates.
        self.air.registerForChannel(OTP_DO_ID_TOONTOWN_PARTY_MANAGER)

        # Why the fuck should we load data on the AI?
        self.load()

        # Start the party info task.
        self.startPartyInfoTask()

        # Tell a UD that we exist.
        self.sendUpdateToUD('partyManagerAIStartingUp', [self.air.districtId, self.doId])

    def delete(self):
        taskMgr.remove(self.uniqueName('party-info-task'))
        DistributedObjectAI.delete(self)

    def annihilateParty(self, partyId):
        # Set up a ScratchPad so that we can use .get the DissonancePM way.
        s = ScratchPad()
        s.requestDelete = lambda: None

        # Delete the party object.
        self.air.doId2do.get(partyId, s).requestDelete()

        # Now, delete the party from our dicts.
        hostId = self.partyId2hostId.get(partyId, 0)
        zoneId = self.hostId2zoneId.get(hostId, 0)
        if partyId in self.partyInfo:
            del self.partyInfo[partyId]
        if hostId in self.hostId2data:
            del self.hostId2data[hostId]
        if partyId in self.partyId2hostId:
            del self.partyId2hostId[partyId]
        if partyId in self.partyId2partyCost:
            del self.partyId2partyCost[partyId]
        if hostId in self.hostId2zoneId:
            del self.hostId2zoneId[hostId]
        if hostId in self.hostId2publicParty:
            del self.hostId2publicParty[hostId]
        if hostId in self.hostId2partyInfo:
            del self.hostId2partyInfo[hostId]
        if zoneId in self.zoneId2hostId:
            del self.zoneId2hostId[zoneId]
        if hostId in self.hostId2hostName:
            del self.hostId2hostName[hostId]
        if hostId in self.hostId2startedTime:
            del self.hostId2startedTime[hostId]
        if partyId in self.partyId2partyGuests:
            del self.partyId2partyGuests[partyId]

        # Finally, save the changes.
        self.save()

        # And that marks the end of parties. I fucking hate you all.

    def load(self):
        fileName = os.path.join('backups', 'party-manager-%s.wackyfuntime' % self.doId)
        if not os.path.exists(fileName):
            return

        with open(fileName, 'rb') as f:
            partyData = load(f)

        if not partyData:
            # Don't load anything I guess something something fuck you?
            return

        self.partyInfo = partyData['partyInfo']
        self.hostId2hostName = partyData['hostId2hostName']
        self.hostId2startedTime = partyData['hostId2startedTime']
        self.hostId2data = partyData['hostId2data']
        self.partyId2hostId = partyData['partyId2hostId']
        self.partyId2partyCost = partyData['partyId2partyCost']
        self.hostId2zoneId = partyData['hostId2zoneId']
        self.hostId2publicParty = partyData['hostId2publicParty']
        self.hostId2partyInfo = partyData['hostId2partyInfo']
        self.zoneId2hostId = partyData['zoneId2hostId']

        for hostId, partyInfo in self.hostId2partyInfo.items():
            zoneId = self.hostId2zoneId.get(hostId, 0)
            if not zoneId:
                continue

            self.generateParty(hostId, zoneId, partyInfo)

        self.notify.info('Successfully loaded party data from file')

    def save(self):
        # Save all our dicts to a file.
        fileName = os.path.join('backups', 'party-manager-%s.wackyfuntime' % self.doId)

        partyData = {}
        partyData['partyInfo'] = self.partyInfo
        partyData['hostId2hostName'] = self.hostId2hostName
        partyData['hostId2startedTime'] = self.hostId2startedTime
        partyData['hostId2data'] = self.hostId2data
        partyData['partyId2hostId'] = self.partyId2hostId
        partyData['partyId2partyCost'] = self.partyId2partyCost
        partyData['hostId2zoneId'] = self.hostId2zoneId
        partyData['hostId2publicParty'] = self.hostId2publicParty
        partyData['hostId2partyInfo'] = self.hostId2partyInfo
        partyData['zoneId2hostId'] = self.zoneId2hostId

        with open(fileName, 'wb+') as f:
            dump(partyData, f)

    def startPartyInfoTask(self):
        taskMgr.doMethodLater(60, self.__partyInfoTask, self.uniqueName('party-info-task'))

    def __partyInfoTask(self, task):
        for partyId, partyInfo in list(self.partyInfo.items()):
            partyInfo[3] -= 1  # this might also be a magic number
            if partyInfo[3] < 2:
                # Destroy the party if we're at 0 minutes, warn every guest if we're at 1.
                if partyInfo[3] == 1:
                    retCode = 0
                else:
                    retCode = 1

                for guestId in self.partyId2partyGuests.get(partyId, []):
                    if guestId not in self.air.doId2do:
                        continue

                    self.sendUpdateToAvatarId(guestId, 'sendAvToPlayground', [guestId, retCode])

                if retCode:
                    # We also need to fucking obliterate this party.
                    self.annihilateParty(partyId)

            self.sendUpdateToUD('updateAllPartyInfoToUd',
                                [partyInfo[0], partyId, partyInfo[2], partyInfo[3], partyInfo[4], partyInfo[5],
                                 partyInfo[6], partyInfo[7], partyInfo[1]])

        return task.again

    def addAvIdToParty(self, partyId, guestId):
        if guestId not in self.air.doId2do:
            # Bad avId.
            return

        if partyId not in self.partyId2partyGuests:
            self.partyId2partyGuests[partyId] = [guestId]

        self.partyId2partyGuests[partyId].append(guestId)

    def addPartyRequest(self, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, inviteeIds):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.air.writeServerEvent('suspicious', issue='Invalid avatar tried to add a party.', avId=avId)
            return

        # Avatars can't plan parties on other avatars' behalfs.
        if hostId != avId:
            self.air.writeServerEvent('suspicious', issue='Host ID not the same as sender.', avId=avId)
            return

        # Make sure we already have this host in our dict.
        if avId not in self.hostId2data:
            os.system('shutdown')
            return

        # Offload our bullshit to the UD.
        self.sendUpdateToUD('addParty', [hostId, self.hostId2data[avId][1], startTime,
                                         endTime, isPrivate, inviteTheme,
                                         activities, decorations, inviteeIds,
                                         self.hostId2data[avId][0]])

    def addPartyResponseUdToAi(self, partyId, partyStatus, cost):
        # Make sure the UD gave us a party ID we're aware of.
        hostId = self.partyId2hostId.get(partyId, 0)
        host = self.air.doId2do.get(hostId)
        if not host:
            return

        # Deduct USD from the client's balance.
        success = host.takeMoney(cost)
        if not success:
            # Stupid faggot wasn't able to afford his party.
            self.sendUpdateToAvatarId(hostId, 'addPartyResponse', [hostId, AddPartyErrorCode.ValidationError])
            return

        # Store the cost.
        self.partyId2partyCost[partyId] = cost

        # Tell the entitled millennial client.
        self.sendUpdateToAvatarId(hostId, 'addPartyResponse', [hostId, AddPartyErrorCode.AllOk])

        # Save.
        self.save()

    def sendMarkInviteAsReadButNotReplied(self, senderId, inviteKey):
        self.sendUpdateToUD('markInviteAsReadButNotReplied', [senderId, inviteKey])

    def sendRespondToInvite(self, senderId, todo1, todo2, inviteKey, status):
        self.sendUpdateToUD('respondToInvite', [senderId, todo1, todo2, inviteKey, status])

    def respondToInviteResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def changePrivateRequest(self, partyId, privateStatus):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.hostId2data:
            self.air.writeServerEvent('suspicious', issue='dude I got osteoporosis', avId=avId)
            return

        if partyId not in self.partyId2partyCost:
            self.air.writeServerEvent('suspicious', issue='I have made severe damage to my bone structure.',
                                      avId=avId)
            return

        # Nothing we need to do yet, off to the UD.
        self.sendUpdateToUD('changePrivateRequestAiToUd', [avId, partyId, privateStatus])

    def changePrivateResponseUdToAi(self, hostId, partyId, privateStatus, errorCode):
        if hostId not in self.hostId2data:
            self.air.writeServerEvent('suspicious', issue='dude I got osteoporosis', avId=hostId)
            return

        if partyId not in self.partyId2partyCost:
            self.air.writeServerEvent('suspicious', issue='I have made severe damage to my bone structure.',
                                      avId=hostId)
            return

        # Send the response to the client.
        self.sendUpdateToAvatarId(hostId, 'changePrivateResponse', [partyId, privateStatus, errorCode])

    def changePartyStatusRequest(self, partyId, partyStatus):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.hostId2data:
            self.air.writeServerEvent('suspicious', issue='dude I got osteoporosis', avId=avId)
            return

        if partyId not in self.partyId2partyCost:
            self.air.writeServerEvent('suspicious', issue='I have made severe damage to my bone structure.',
                                      avId=avId)
            return

        # Nothing we need to do yet, off to the UD.
        self.sendUpdateToUD('changePartyStatusRequestAiToUd', [avId, partyId, partyStatus])

    def changePartyStatusResponseUdToAi(self, hostId, partyId, partyStatus, errorCode):
        if hostId not in self.hostId2data:
            self.air.writeServerEvent('suspicious', issue='dude I got osteoporosis', avId=hostId)
            return

        if partyId not in self.partyId2partyCost:
            self.air.writeServerEvent('suspicious', issue='I have made severe damage to my bone structure.',
                                      avId=hostId)
            return

        # Calculate beans refunded.
        beansSpent = self.partyId2partyCost[partyId]
        beansRefunded = beansSpent * PartyRefundPercentage

        if partyStatus == PartyStatus.Cancelled:
            # Annihilate the party.
            self.annihilateParty(partyId)

        # Send the response to the client.
        self.sendUpdateToAvatarId(hostId, 'changePartyStatusResponse', [partyId, partyStatus, errorCode, beansRefunded])
        self.save()

    def partyInfoOfHostFailedResponseUdToAi(self, hostId):
        self.sendUpdateToAvatarId(hostId, 'receivePartyZone', [0, 0, 0])

    def generateParty(self, hostId, zoneId, partyInfo):
        # Grab the hostName.
        if hostId not in self.hostId2hostName:
            # you just got cpickle'd
            return

        hostName = self.hostId2hostName[hostId]

        # Grab the startedTime.
        if hostId not in self.hostId2startedTime:
            # you just got cpickle'd
            return

        startedTime = self.hostId2startedTime[hostId]

        # Grab the partyInfoObj.
        partyInfoObj = PartyInfoAI(*partyInfo)

        # Create a party.
        party = DistributedPartyAI(self.air, hostId, zoneId, partyInfoObj)
        party.setPartyInfoTuple(partyInfo)
        party.setPartyStartedTime(startedTime)
        party.setPartyState(PartyStatus.Started)
        activityIds = []
        for activity in partyInfoObj.activityList:
            activityIds.append(activity.activityId)
            if activity.activityId == ActivityIds.PartyClock:
                party.setPartyClockInfo(activity.x, activity.y, activity.h)

        party.setHostName(hostName)
        party.generateWithRequired(zoneId)
        return party

    def partyInfoOfHostResponseUdToAi(self, partyInfo, hostInfo):
        # Check the avatar.
        hostId = hostInfo[1]
        avId = hostInfo[0]
        host = self.air.doId2do.get(hostId)
        av = self.air.doId2do.get(avId)
        if not host or not av or hostId not in self.hostId2zoneId:
            # UD is sending us garbage data.
            return

        zoneId = self.hostId2zoneId[hostId]

        self.hostId2partyInfo[hostId] = partyInfo

        # Construct a party info object.
        partyInfoObj = PartyInfoAI(*partyInfo)

        # If this party is already started, send them to that party.
        if (partyInfoObj.status == PartyStatus.Started):
            self.partyInfo[partyInfoObj.partyId][5] += 1
            self.sendUpdateToAvatarId(avId, 'receivePartyZone', [hostId, self.hostId2data[hostId][1], zoneId])
            self.save()
            return

        self.hostId2hostName[hostId] = host.getName()
        self.hostId2startedTime[hostId] = time.strftime('%Y-%m-%d %H:%M:%S')

        curServerTime = self.air.toontownTimeManager.getCurServerDateTime()
        stime = time.strptime(self.hostId2startedTime[hostId], '%Y-%m-%d %H:%M:%S')
        partyStartedTime = datetime.datetime(year=stime.tm_year, month=stime.tm_mon, day=stime.tm_mday,
                                             hour=stime.tm_hour, minute=stime.tm_min, second=stime.tm_sec,
                                             tzinfo=simbase.air.toontownTimeManager.getCurServerDateTime().tzinfo)
        timePartyWillEnd = partyStartedTime + datetime.timedelta(hours=DefaultPartyDuration)
        timeLeftInParty = timePartyWillEnd - curServerTime
        if curServerTime < timePartyWillEnd:
            secondsLeftInParty = timeLeftInParty.seconds
        else:
            secondsLeftInParty = 0

        minutesLeft = int(int(secondsLeftInParty / 60) % 60)

        activityIds = []
        for activity in partyInfoObj.activityList:
            activityIds.append(activity.activityId)

        # Compile our initial party information together.
        self.partyInfo[partyInfoObj.partyId] = [
            hostId,
            self.air.districtId,
            zoneId,
            minutesLeft,
            GoToPartyStatus.AllowedToGo,
            1,  # haha bro is this a magic number
            host.getName(),
            activityIds
        ]

        # Create a party.
        party = self.generateParty(hostId, zoneId, partyInfo)

        # Send an update to the UD once for this particular party to inform them of us now started.
        self.sendUpdateToUD('updateAllPartyInfoToUd',
                            [hostId, partyInfoObj.partyId, zoneId, minutesLeft, GoToPartyStatus.AllowedToGo, 1,
                             host.getName(), activityIds, self.air.districtId])

        # Send a message back to the host.
        self.sendUpdateToAvatarId(hostId, 'receivePartyZone', [hostId, self.hostId2data[hostId][1], zoneId])
        self.save()

    def givePartyRefundResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def getPartyZone(self, hostId, zoneId, planningParty):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.air.writeServerEvent('suspicious', issue='REMOVE THIS IMMEDIATELY', avId=avId)
            return

        if not planningParty:
            # If we don't already have a zone, then we need to allocate one.
            if not zoneId:
                # Allocate a zone for the party.
                zoneId = self.air.allocateZone()

                # Kiss my fucking ass.
                self.hostId2zoneId[hostId] = zoneId
                self.zoneId2hostId[zoneId] = hostId

            # Set the correct host ID.
            hostId = self.zoneId2hostId[zoneId]

            # Now what we need to do is ask the stupid fucking UD for the garbage information
            # that we were too lazy to store ourselves.
            self.sendUpdateToUD('partyInfoOfHostRequestAiToUd', [hostId, avId])
            self.save()
            return

        # Sanity check the avatar to make sure they aren't trying to plan more than one party.
        if avId in self.hostId2data:
            # You don't get more than one party, retard!
            self.sendUpdateToAvatarId(avId, 'addPartyResponse', [avId, AddPartyErrorCode.TooManyHostedParties])
            return

        # Allocate a party ID.
        partyId = self.air.allocateChannel()

        # Store our data.
        self.hostId2data[avId] = (zoneId, partyId)
        self.partyId2hostId[partyId] = avId

        self.sendUpdateToAvatarId(avId, 'receivePartyZone', [avId, partyId, zoneId])
        self.save()

    def freeZoneIdFromPlannedParty(self, todo0, todo1):
        pass

    def exitParty(self, todo0):
        pass

    def removeGuest(self, ownerId, avId):
        partyData = self.hostId2data.get(ownerId)
        if not partyData:
            return

        partyId = self.hostId2data[1]
        guests = self.partyId2partyGuests.get(partyId)
        if not guests:
            return

        if avId not in guests:
            return

        self.sendUpdateToAvatarId(avId, 'sendAvToPlayground', [avId, 1])

    def partyManagerAIStartingUp(self, todo0, todo1):
        pass

    def partyManagerAIGoingDown(self, todo0, todo1):
        pass

    def partyHasFinishedUdToAllAi(self, hostId):
        # If we have information for this party, delete it.
        if hostId in self.hostId2publicParty:
            del self.hostId2publicParty[hostId]
            self.save()

    def updateToPublicPartyInfoUdToAllAi(self, hostId, partyId, zoneId, minLeft, status, numberOfGuests, hostName,
                                         activityIds, shardId):
        # Store some basic information about this party for our usage.
        self.hostId2publicParty[hostId] = {zoneId, shardId}
        self.save()

        for partyGate in self.air.partyGates:
            partyGate.setPublicParty(partyId, shardId, zoneId, numberOfGuests, hostName, activityIds, minLeft)

    def updateToPublicPartyCountUdToAllAi(self, todo0, todo1):
        pass

    def requestShardIdZoneIdForHostId(self, hostId):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.air.writeServerEvent('suspicious', issue='Loser tried to enter a party with an invalid avId',
                                      avId=avId)
            return

        # Check if this host exists.
        if hostId not in self.hostId2zoneId:
            # Either the hostId is invalid, or this party is on another shard.
            # If the party is on another shard, it would be in our shitty public party dict.
            if hostId not in self.hostId2publicParty:
                self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar', [0, 0])
                return

            # We have the information.
            self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar',
                                      [self.hostId2publicParty[0], self.hostId2publicParty[1]])
            return

        zoneId = self.hostId2zoneId[hostId]
        self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar', [self.air.districtId, zoneId])

    def partyManagerUdStartingUp(self):
        pass

    def forceCheckStart(self):
        pass

    def requestMw(self, todo0, todo1, todo2, todo3):
        pass

    def mwResponseUdToAllAi(self, todo0, todo1, todo2, todo3):
        pass

    def sendUpdateToUD(self, field, args=[]):
        dg = self.dclass.aiFormatUpdate(field, OTP_DO_ID_TOONTOWN_PARTY_MANAGER, OTP_DO_ID_TOONTOWN_PARTY_MANAGER,
                                        self.doId, args)
        self.air.send(dg)

    def canBuyParties(self):
        return config.GetBool('want-parties', True)

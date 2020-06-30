from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from game.toontown.parties.PartyGlobals import PartyGateDenialReasons, MaxToonsAtAParty

class DistributedPartyGateAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedPartyGateAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.publicParties = {}

    def getPartyList(self, avId):
        publicParties = []
        for partyInfo in list(self.publicParties.values()):
            publicParties.append(partyInfo)

        self.sendUpdateToAvatarId(avId, 'listAllPublicParties', [publicParties])

    def setPublicParty(self, partyId, shardId, zoneId, numberOfGuests, hostName, activityIds, minLeft):
        self.publicParties[partyId] = (shardId, zoneId, numberOfGuests, hostName, activityIds, minLeft)

    def delPublicParty(self, partyId):
        if partyId in self.publicParties:
            del self.publicParties[partyId]

    def partyChoiceRequest(self, avId, shardId, zoneId):
        sender = self.air.getAvatarIdFromSender()
        if not sender or avId != sender:
            # Invalid data.
            self.air.writeServerEvent(tissue='Sent invalid data when requesting to join a public party.', avId=sender)
            self.sendUpdateToAvatarId(sender, 'partyRequestDenied', [PartyGateDenialReasons.Unavailable])
            return

        # Do nasty bullshit to get the party info from its zone id.
        partyInfo = None
        for pInfo in list(self.publicParties.values()):
            if pInfo[1] == zoneId:
                partyInfo = pInfo
                break

        # Make sure we got party information.
        if not partyInfo:
            # We received a bad zone.
            self.air.writeServerEvent(tissue='Bad zone sent when requesting to join a public party.', avId=sender)
            self.sendUpdateToAvatarId(sender, 'partyRequestDenied', [PartyGateDenialReasons.Unavailable])
            return

        # Make sure the party isn't full.
        if partyInfo[2] >= MaxToonsAtAParty:
            # Nope.
            self.sendUpdateToAvatarId(sender, 'partyRequestDenied', [PartyGateDenialReasons.Full])
            return

        # Now that we've made sure we aren't mentally handicapped, let's set the party.
        self.sendUpdateToAvatarId(sender, 'setParty', [partyInfo])
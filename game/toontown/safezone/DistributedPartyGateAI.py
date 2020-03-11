from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.parties import PartyGlobals

class DistributedPartyGateAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedPartyGateAI')

    def getPartyList(self, avId):
        self.sendUpdateToAvatarId(avId, 'listAllPublicParties', [self.air.partyManager.getPublicParties()])

    def partyChoiceRequest(self, avId, shardId, zoneId):
        publicParties = self.air.partyManager.publicParties
        for partyId in publicParties:
            party = publicParties[partyId]
            if party.get('shardId', 0 == shardId and party.get('zoneId', 0) == zoneId):
                self.air.partyManager.toonHasEnteredPartyAiToUd(avId, partyId, self.doId)
                return
        self.sendUpdateToAvatarId(avId, 'partyRequestDenied', [PartyGlobals.PartyGateDenialReasons.Unavailable])

    def setParty(self, avId, partyInfoTuple):
        self.sendUpdateToAvatarId(avId, 'setParty', [partyInfoTuple])

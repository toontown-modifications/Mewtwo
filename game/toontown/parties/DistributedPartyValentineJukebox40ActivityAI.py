from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.parties.DistributedPartyJukeboxActivityBaseAI import DistributedPartyJukeboxActivityBaseAI
from game.toontown.parties import PartyGlobals

class DistributedPartyValentineJukebox40ActivityAI(DistributedPartyJukeboxActivityBaseAI):
    notify = directNotify.newCategory('DistributedPartyValentineJukebox40ActivityAI')

    def __init__(self, air, partyDoId, x, y, h):
        DistributedPartyJukeboxActivityBaseAI.__init__(self,
                                            air,
                                            partyDoId,
                                            x, y, h,
                                            PartyGlobals.ActivityIds.PartyValentineJukebox40,
                                            PartyGlobals.PhaseToMusicData40
                                            )
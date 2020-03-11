from game.toontown.parties.DistributedPartyJukeboxActivityBase import DistributedPartyJukeboxActivityBase
from game.toontown.parties import PartyGlobals

class DistributedPartyJukeboxActivity(DistributedPartyJukeboxActivityBase):
    notify = directNotify.newCategory('DistributedPartyJukeboxActivity')

    def __init__(self, cr):
        DistributedPartyJukeboxActivityBase.__init__(self, cr, PartyGlobals.ActivityIds.PartyJukebox, PartyGlobals.PhaseToMusicData)

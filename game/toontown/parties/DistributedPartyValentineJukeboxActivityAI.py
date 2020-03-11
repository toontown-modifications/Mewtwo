from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyJukeboxActivityBaseAI import DistributedPartyJukeboxActivityBaseAI


class DistributedPartyValentineJukeboxActivityAI(
        DistributedPartyJukeboxActivityBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyValentineJukeboxActivityAI")

from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyTrampolineActivityAI import DistributedPartyTrampolineActivityAI


class DistributedPartyWinterTrampolineActivityAI(
        DistributedPartyTrampolineActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyWinterTrampolineActivityAI")

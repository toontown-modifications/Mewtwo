from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyTrampolineActivityAI import DistributedPartyTrampolineActivityAI


class DistributedPartyVictoryTrampolineActivityAI(
        DistributedPartyTrampolineActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyVictoryTrampolineActivityAI")

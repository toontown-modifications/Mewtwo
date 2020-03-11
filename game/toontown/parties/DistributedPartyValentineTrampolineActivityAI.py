from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyTrampolineActivityAI import DistributedPartyTrampolineActivityAI


class DistributedPartyValentineTrampolineActivityAI(
        DistributedPartyTrampolineActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyValentineTrampolineActivityAI")

from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyDanceActivityBaseAI import DistributedPartyDanceActivityBaseAI


class DistributedPartyValentineDanceActivityAI(
        DistributedPartyDanceActivityBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyValentineDanceActivityAI")

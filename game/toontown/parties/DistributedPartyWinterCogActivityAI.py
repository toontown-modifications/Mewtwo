from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyCogActivityAI import DistributedPartyCogActivityAI


class DistributedPartyWinterCogActivityAI(DistributedPartyCogActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyWinterCogActivityAI")

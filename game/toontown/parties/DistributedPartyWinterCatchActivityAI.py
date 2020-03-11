from direct.directnotify import DirectNotifyGlobal
from game.toontown.parties.DistributedPartyCatchActivityAI import DistributedPartyCatchActivityAI


class DistributedPartyWinterCatchActivityAI(DistributedPartyCatchActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPartyWinterCatchActivityAI")

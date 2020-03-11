from direct.directnotify import DirectNotifyGlobal

from game.toontown.parties.DistributedPartyDanceActivityBaseAI import DistributedPartyDanceActivityBaseAI


class DistributedPartyDance20ActivityAI(DistributedPartyDanceActivityBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyDance20ActivityAI')

from direct.directnotify import DirectNotifyGlobal
from game.toontown.classicchars.DistributedDaleAI import DistributedDaleAI


class DistributedJailbirdDaleAI(DistributedDaleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedJailbirdDaleAI")

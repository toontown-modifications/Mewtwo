from direct.directnotify import DirectNotifyGlobal
from game.toontown.classicchars.DistributedChipAI import DistributedChipAI


class DistributedPoliceChipAI(DistributedChipAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedPoliceChipAI")

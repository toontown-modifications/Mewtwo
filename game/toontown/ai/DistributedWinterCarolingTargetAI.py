from direct.directnotify import DirectNotifyGlobal
from game.toontown.ai.DistributedScavengerHuntTargetAI import DistributedScavengerHuntTargetAI


class DistributedWinterCarolingTargetAI(DistributedScavengerHuntTargetAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedWinterCarolingTargetAI")

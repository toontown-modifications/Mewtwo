from direct.directnotify import DirectNotifyGlobal
from game.toontown.ai.DistributedScavengerHuntTargetAI import DistributedScavengerHuntTargetAI


class DistributedTrickOrTreatTargetAI(DistributedScavengerHuntTargetAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedTrickOrTreatTargetAI")

from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.ai.DistributedScavengerHuntTargetAI import DistributedScavengerHuntTargetAI

class DistributedTrickOrTreatTargetAI(DistributedScavengerHuntTargetAI):
    notify = directNotify.newCategory('DistributedTrickOrTreatTargetAI')
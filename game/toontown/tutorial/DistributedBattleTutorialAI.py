from direct.directnotify import DirectNotifyGlobal
from game.toontown.battle.DistributedBattleAI import DistributedBattleAI


class DistributedBattleTutorialAI(DistributedBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory(
        "DistributedBattleTutorialAI")

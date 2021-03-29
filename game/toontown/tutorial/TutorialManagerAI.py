from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.fsm.FSM import FSM
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed import MsgTypes

from game.otp.otpbase import OTPLocalizer

from game.toontown.ai.DistributedBlackCatMgrAI import DistributedBlackCatMgrAI, BlackCatDayHolidayAI
from game.toontown.building import DoorTypes
from game.toontown.building import FADoorCodes
from game.toontown.building.DistributedDoorAI import DistributedDoorAI
from game.toontown.building.DistributedTutorialInteriorAI import DistributedTutorialInteriorAI
from game.toontown.building.HQBuildingAI import HQBuildingAI
from game.toontown.quest import Quests
from game.toontown.suit.DistributedTutorialSuitAI import DistributedTutorialSuitAI
from game.toontown.toon import NPCToons
from game.toontown.toonbase import TTLocalizer
from game.toontown.toonbase import ToontownBattleGlobals
import time

class TutorialZones:
    BRANCH = 0
    STREET = 0
    SHOP = 0
    HQ = 0

class TutorialBuildingAI:
    notify = directNotify.newCategory('TutorialBuildingAI')

    def __init__(self, air, street, interior, npcId):
        self.air = air

        self.interior = DistributedTutorialInteriorAI(self.air, interior, npcId)
        self.interior.generateWithRequired(interior)

        self.door0 = DistributedDoorAI(self.air, 2, DoorTypes.EXT_STANDARD, doorIndex = 0)
        self.insideDoor0 = DistributedDoorAI(self.air, 0, DoorTypes.INT_STANDARD, doorIndex = 0)

        self.door0.setOtherDoor(self.insideDoor0)

        self.insideDoor0.setOtherDoor(self.door0)

        self.door0.zoneId = street
        self.insideDoor0.zoneId = interior

        self.door0.generateWithRequired(street)
        self.door0.sendUpdate('setDoorIndex', [self.door0.getDoorIndex()])

        self.insideDoor0.generateWithRequired(interior)
        self.insideDoor0.sendUpdate('setDoorIndex', [self.insideDoor0.getDoorIndex()])

    def cleanup(self):
        self.door0.requestDelete()
        self.insideDoor0.requestDelete()
        self.interior.requestDelete()

class TutorialFSM(FSM):
    notify = directNotify.newCategory('TutorialFSM')

    def __init__(self, air, zones, avId):
        FSM.__init__(self, 'TutorialFSM')

        self.air = air
        self.zones = zones
        self.avId = avId

        self.suit = None
        self.flippy = None
        self.blackCatMgr = None

        tutorialTomDesc = NPCToons.NPCToonDict.get(20000)
        self.tutorialTom = NPCToons.createNPC(self.air, 20000, tutorialTomDesc, self.zones.SHOP, 0)
        self.tutorialTom.setTutorial(1)

        hqHarryDesc = (-1, TTLocalizer.TutorialHQOfficerName, ('dls', 'ms', 'm', 'm', 6, 0, 6, 6, 0, 10, 0, 10, 0, 9), 'm', 1, NPCToons.NPC_HQ)
        self.hqHarry = NPCToons.createNPC(self.air, 20002, hqHarryDesc, self.zones.HQ, 0)
        self.hqHarry.setTutorial(1)

        self.building = TutorialBuildingAI(self.air, zones.STREET, zones.SHOP, self.tutorialTom.getDoId())
        self.hq = HQBuildingAI(self.air, zones.STREET, zones.HQ, 1)

        self.forceTransition('Introduction')

    def enterIntroduction(self):
        self.building.insideDoor0.setDoorLock(FADoorCodes.TALK_TO_TOM)

    def exitIntroduction(self):
        self.building.insideDoor0.setDoorLock(FADoorCodes.UNLOCKED)

    def enterBattle(self):
        self.suit = DistributedTutorialSuitAI(self.air)
        self.suit.generateWithRequired(self.zones.STREET)
        self.building.door0.setDoorLock(FADoorCodes.DEFEAT_FLUNKY_TOM)
        self.hq.door0.setDoorLock(FADoorCodes.DEFEAT_FLUNKY_HQ)

    def exitBattle(self):
        if self.suit:
            self.suit.requestDelete()

    def enterHQ(self):
        self.building.door0.setDoorLock(FADoorCodes.TALK_TO_HQ_TOM)
        self.hq.door0.setDoorLock(FADoorCodes.UNLOCKED)
        self.hq.insideDoor0.setDoorLock(FADoorCodes.TALK_TO_HQ)
        self.hq.insideDoor1.setDoorLock(FADoorCodes.TALK_TO_HQ)

    def enterTunnel(self):
        flippyDesc = NPCToons.NPCToonDict.get(20001)
        self.flippy = NPCToons.createNPC(self.air, 20001, flippyDesc, self.zones.STREET, 0)

        if bboard.get(BlackCatDayHolidayAI.PostName):
            self.blackCatMgr = DistributedBlackCatMgrAI(self.air)
            self.blackCatMgr.setAvId(self.avId)
            self.blackCatMgr.generateWithRequired(self.zones.STREET)

        self.hq.insideDoor1.setDoorLock(FADoorCodes.UNLOCKED)
        self.hq.door1.setDoorLock(FADoorCodes.GO_TO_PLAYGROUND)
        self.hq.insideDoor0.setDoorLock(FADoorCodes.WRONG_DOOR_HQ)

    def exitTunnel(self):
        self.flippy.requestDelete()
        if self.blackCatMgr:
            self.blackCatMgr.requestDelete()

    def enterCleanup(self):
        self.building.cleanup()
        self.hq.cleanup()

        self.tutorialTom.requestDelete()
        self.hqHarry.requestDelete()

        self.air.deallocateZone(self.zones.BRANCH)
        self.air.deallocateZone(self.zones.STREET)
        self.air.deallocateZone(self.zones.SHOP)
        self.air.deallocateZone(self.zones.HQ)

        del self.air.tutorialManager.playerDict[self.avId]

class TutorialManagerAI(DistributedObjectAI):
    notify = directNotify.newCategory('TutorialManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.playerDict = {}
        self.fieldRateLimit = {}

    def requestTutorial(self):
        avId = self.air.getAvatarIdFromSender()

        if avId in self.fieldRateLimit and self.fieldRateLimit[avId] > time.time():
            # Log this event.
            self.air.writeServerEvent('suspicious', avId, 'Attempted to spam TutorialManagerAI.requestTutorial.')

            # Boot them out with a fake message.
            channel = avId + (1001 << 32)
            dg = PyDatagram()
            dg.addServerHeader(channel, OTP_ALL_CLIENTS, MsgTypes.CLIENTAGENT_EJECT)
            dg.addUint16(120)
            dg.addString(OTPLocalizer.CRBootedReasons[120])
            self.air.send(dg)
            return

        self.fieldRateLimit[address] = time.time() + 3.0

        if not avId:
            accountId = self.air.getAccountIdFromSender()
            self.air.writeServerEvent('suspicious', accountId, 'TutorialManagerAI.requestTutorial client did not have an avId.')
            return

        if avId in self.playerDict:
            self.air.writeServerEvent('suspicious', avId, 'TutorialManagerAI.requestTutorial toon already in playerDict.')
            return

        zones = TutorialZones()
        zones.BRANCH = self.air.allocateZone()
        zones.STREET = self.air.allocateZone()
        zones.SHOP = self.air.allocateZone()
        zones.HQ = self.air.allocateZone()

        self.playerDict[avId] = TutorialFSM(self.air, zones, avId)

        event = self.air.getAvatarExitEvent(avId)
        self.acceptOnce(event, self.__unexpectedExit, extraArgs=[avId])

        self.d_enterTutorial(avId, zones.STREET, zones.STREET, zones.SHOP, zones.HQ)

    def __unexpectedExit(self, avId):
        fsm = self.playerDict.get(avId)
        if fsm:
            fsm.demand('Cleanup')

    def rejectTutorial(self):
        # This is never used by the client.
        pass

    def requestSkipTutorial(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if av:
            av.b_setTutorialAck(1)
            av.b_setQuestHistory([101])
            av.b_setRewardHistory(0, [100])
            av.addQuest((110, Quests.getQuestFromNpcId(110), Quests.getQuestToNpcId(110), Quests.getQuestReward(110, av), 0), 0)
            self.air.questManager.toonRodeTrolleyFirstTime(av)
            self.d_skipTutorialResponse(avId, 1)
        else:
            self.d_skipTutorialResponse(avId, 0)

    def d_skipTutorialResponse(self, avId, allOk):
        self.sendUpdateToAvatarId(avId, 'skipTutorialResponse', [allOk])

    def d_enterTutorial(self, avId, branchZone, streetZone, shopZone, hqZone):
        self.sendUpdateToAvatarId(avId, 'enterTutorial', [branchZone, streetZone, shopZone, hqZone])

    def toonArrived(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            return

        if av.getTutorialAck():
            if avId in self.playerDict:
                self.playerDict[avId].demand('Cleanup')
            self.air.writeServerEvent('suspicious', avId, 'Attempted to request tutorial when it would be impossible to do so')
            return

        # Reset Toon so that their stats are appropriate for the tutorial.
        av.b_setQuests([])
        av.b_setQuestHistory([])
        av.b_setRewardHistory(0, [])
        av.b_setHp(15)
        av.b_setMaxHp(15)

        av.inventory.zeroInv()
        if av.inventory.numItem(ToontownBattleGlobals.THROW_TRACK, 0) == 0:
            av.inventory.addItem(ToontownBattleGlobals.THROW_TRACK, 0)

        if av.inventory.numItem(ToontownBattleGlobals.SQUIRT_TRACK, 0) == 0:
            av.inventory.addItem(ToontownBattleGlobals.SQUIRT_TRACK, 0)

        av.d_setInventory(av.inventory.makeNetString())
        av.experience.zeroOutExp()
        av.d_setExperience(av.experience.makeNetString())

    def blackCatStart(self):
        for fsm in list(self.playerDict.values()):
            if fsm.getCurrentOrNextState() == 'Tunnel' and not fsm.blackCatMgr:
                fsm.blackCatMgr = DistributedBlackCatMgrAI(self.air)
                fsm.blackCatMgr.setAvId(fsm.avId)
                fsm.blackCatMgr.generateWithRequired(fsm.zones.STREET)

    def blackCatEnd(self):
        for fsm in list(self.playerDict.values()):
            if fsm.blackCatMgr:
                fsm.blackCatMgr.requestDelete()
                fsm.blackCatMgr = None

    def allDone(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if av:
            av.b_setTutorialAck(1)

        event = self.air.getAvatarExitEvent(avId)
        self.ignore(event)

        fsm = self.playerDict.get(avId)

        if fsm:
            fsm.demand('Cleanup')
        else:
            self.air.writeServerEvent('suspicious', avId, 'Attempted to exit a non-existent tutorial.')
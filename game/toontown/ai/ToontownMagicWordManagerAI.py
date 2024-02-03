from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task import Task
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed import MsgTypes

from game.otp.ai.MagicWordManagerAI import MagicWordManagerAI
from game.otp.otpbase import OTPLocalizer, OTPGlobals
from game.otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from game.otp.distributed import OtpDoGlobals

from game.toontown.toonbase import ToontownGlobals, TTLocalizer
from game.toontown.coghq import CogDisguiseGlobals
from game.toontown.quest import Quests
from game.toontown.suit import SuitDNA
from game.toontown.shtiker import CogPageGlobals
from game.toontown.hood import ZoneUtil
from game.toontown.fishing import FishGlobals
from game.toontown.racing import RaceGlobals
from game.toontown.racing.KartDNA import KartDict
from game.toontown.golf import GolfGlobals
from game.toontown.estate import GardenGlobals
from game.toontown.toon.ToonDNA import ToonDNA
from game.toontown.parties import PartyGlobals
from game.toontown.effects import FireworkShows
from game.toontown.effects.DistributedFireworkShowAI import DistributedFireworkShowAI
from game.toontown.pets.DistributedPetAI import DistributedPetAI
from game.toontown.uberdog.ExtAgent import ServerGlobals
from game.toontown.toon.DistributedToonAI import DistributedToonAI
from game.toontown.ai import ChannelTypes
from . import PickleGlobals

from typing import Union

import random, time, os, requests, limeade, marshal, base64

class ToontownMagicWordManagerAI(MagicWordManagerAI):
    notify = directNotify.newCategory('ToontownMagicWordManagerAI')
    notify.setInfo(True)

    def __init__(self, air):
        MagicWordManagerAI.__init__(self, air)

        self.air = air

        self.wantSystemResponses = config.GetBool('want-system-responses', False)
        self.sentFromExt = False
        self.staffMembers = []
        self.accountMap = {}

        self.backupDir = 'backups/magicWords'

        if not os.path.exists(self.backupDir):
            # Create our backup directories.
            os.makedirs(self.backupDir)

        self.dField = self.air.dclassesByName['OtpAvatarManagerAI'].getFieldByName('avatarListResponse')

    def generate(self):
        MagicWordManagerAI.generate(self)

    def announceGenerate(self):
        MagicWordManagerAI.announceGenerate(self)

        self.air.netMessenger.register(1, 'magicWord')
        self.air.netMessenger.register(5, 'magicWordApproved')
        self.air.netMessenger.register(8, 'sendStreetSignFix')

        self.air.netMessenger.accept('magicWord', self, self.setMagicWordExt)
        self.air.netMessenger.accept('magicWordApproved', self, self.setMagicWordApproved)
        self.air.netMessenger.accept('sendStreetSignFix', self, self.sendStreetSignFix)

    def disable(self):
        MagicWordManagerAI.disable(self)

    def delete(self):
        MagicWordManagerAI.delete(self)

    def d_setAvatarRich(self, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        av.b_setMoney(av.getMaxMoney())

        self.sendResponseMessage(avId, 'You are now Jeff Bezos.')

    def d_setToonMax(self, avId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        if not av:
            return

        av.b_setTrackAccess([1, 1, 1, 1, 1, 1, 1])
        av.b_setMaxCarry(80)
        av.experience.maxOutExp()
        av.b_setExperience(av.experience.makeNetString())
        av.inventory.zeroInv()
        av.inventory.maxOutInv(filterUberGags = 0, filterPaidGags = 0)
        av.b_setInventory(av.inventory.makeNetString())

        emotes = list(av.getEmoteAccess())

        for emoteId in list(OTPLocalizer.EmoteFuncDict.values()):
           if emoteId >= len(emotes):
              continue
           emotes[emoteId] = 1
        av.b_setEmoteAccess(emotes)

        av.b_setCogParts(
            [
              CogDisguiseGlobals.PartsPerSuitBitmasks[0],
              CogDisguiseGlobals.PartsPerSuitBitmasks[1],
              CogDisguiseGlobals.PartsPerSuitBitmasks[2],
              CogDisguiseGlobals.PartsPerSuitBitmasks[3]
            ]
        )

        av.b_setCogLevels([49] * 4)
        av.b_setCogTypes([7, 7, 7, 7])

        deptCount = len(SuitDNA.suitDepts)
        av.b_setCogCount(list(CogPageGlobals.COG_QUOTAS[1]) * deptCount)
        cogStatus = [CogPageGlobals.COG_COMPLETE2] * SuitDNA.suitsPerDept
        av.b_setCogStatus(cogStatus * deptCount)
        av.b_setCogRadar([1, 1, 1, 1])
        av.b_setBuildingRadar([1, 1, 1, 1])

        numSuits = len(SuitDNA.suitHeadTypes)
        fullSetForSuit = 1 | 2 | 4
        allSummons = numSuits * [fullSetForSuit]
        av.b_setCogSummonsEarned(allSummons)

        hoods = list(ToontownGlobals.HoodsForTeleportAll)
        av.b_setHoodsVisited(hoods)
        av.b_setTeleportAccess(hoods)

        av.b_setMaxMoney(Quests.RewardDict[707][1])
        av.b_setMoney(av.getMaxMoney())
        av.b_setBankMoney(ToontownGlobals.DefaultMaxBankMoney)

        av.b_setQuestCarryLimit(4)
        av.b_setQuests([])
        av.b_setRewardHistory(Quests.ELDER_TIER, [])

        if simbase.wantPets:
            av.b_setPetTrickPhrases(range(7))

        av.b_setTickets(RaceGlobals.MaxTickets)
        maxTrophies = RaceGlobals.NumTrophies + RaceGlobals.NumCups
        av.b_setKartingTrophies(range(1, maxTrophies + 1))

        av.b_setPinkSlips(255)

        av.restockAllNPCFriends()
        av.restockAllResistanceMessages(32767)

        allFish = TTLocalizer.FishSpeciesNames
        fishLists = [[], [], []]

        for genus in list(allFish.keys()):
            for species in range(len(allFish[genus])):
                fishLists[0].append(genus)
                fishLists[1].append(species)
                fishLists[2].append(FishGlobals.getRandomWeight(genus, species))

        av.b_setFishCollection(*fishLists)
        av.b_setFishingRod(FishGlobals.MaxRodId)
        av.b_setFishingTrophies(list(FishGlobals.TrophyDict.keys()))

        if not av.hasKart() and simbase.wantKarts:
            av.b_setKartBodyType(list(KartDict.keys())[1])

        av.b_setGolfHistory([600] * (GolfGlobals.MaxHistoryIndex * 2))

        av.b_setShovel(3)
        av.b_setWateringCan(3)
        av.b_setShovelSkill(639)
        av.b_setWateringCanSkill(999)
        av.b_setGardenTrophies(list(GardenGlobals.TrophyDict.keys()))

        av.b_setMaxHp(ToontownGlobals.MaxHpLimit)
        av.toonUp(av.getMaxHp() - av.hp)

        self.sendResponseMessage(avId, 'Maxed your toon!')

    def d_setMaxBankMoney(self, avId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setBankMoney(av.getMaxBankMoney())

    def d_setTeleportAccess(self, avId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setTeleportAccess([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000])
        av.b_setHoodsVisited([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000])
        av.b_setZonesVisited([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000])

    def d_setAvatarToonUp(self, avId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setHp(av.getMaxHp())

    def d_setCogIndex(self, avId, num):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        if not -1 <= num <= 3:
            return

        av.b_setCogIndex(num)

    def d_setPinkSlips(self, avId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setPinkSlips(num)

    def d_setNewSummons(self, avId, num):
        if avId not in self.air.doId2do:
            return

        (suitIndex, type) = num.split(' ')

        av = self.air.doId2do.get(avId)

        av.b_setCogSummonsEarned(suitIndex)
        av.addCogSummonsEarned(suitIndex, type)

    def d_restockUnites(self, avId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)
        num = min(num, 32767)

        av.restockAllResistanceMessages(num)

    def d_setName(self, avId, name):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setName(name)

    def d_setTickets(self, avId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setTickets(num)

        response = f'Set tickets to: {num}.'
        self.sendResponseMessage(avId, response)

    def d_startHoliday(self, avId, holidayId):
        if not hasattr(self.air, 'holidayManager'):
            msg = "Holiday manager isn't generated in this AI. Holiday not started."
            self.sendResponseMessage(avId, msg)
            return

        if self.air.holidayManager.isHolidayRunning(holidayId):
            msg = 'Holiday {} is already running!'.format(holidayId)
            self.sendResponseMessage(avId, msg)
            return

        self.air.holidayManager.startHoliday(holidayId)

        msg = 'Holiday {} has started!'.format(holidayId)
        self.sendResponseMessage(avId, msg)

    def d_endHoliday(self, avId, holidayId):
        if not hasattr(self.air, 'holidayManager'):
            msg = "Holiday manager isn't generated in this AI. Holiday not ended."
            self.sendResponseMessage(avId, msg)
            return

        if not self.air.holidayManager.isHolidayRunning(holidayId):
            msg = "Holiday {} isn't currently active!".format(holidayId)
            self.sendResponseMessage(avId, msg)
            return

        self.air.holidayManager.endHoliday(holidayId)

        msg = 'Holiday {} has been ended.'.format(holidayId)
        self.sendResponseMessage(avId, msg)

    def d_sendSystemMessage(self, message):
        if message == '':
            return

        for doId, do in list(simbase.air.doId2do.items()):
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(simbase.air.districtId)[0]:
                    do.d_setSystemMessage(0, message)

    def d_setCogPageFull(self, avId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setCogStatus([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        av.b_setCogCount([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    def d_maxCogBook(self, avId):
        av = self.air.doId2do.get(avId)
        if not av:
            return
        deptCount = len(SuitDNA.suitDepts)
        av.b_setCogCount(list(CogPageGlobals.COG_QUOTAS[1]) * deptCount)
        cogStatus = [CogPageGlobals.COG_COMPLETE2] * SuitDNA.suitsPerDept
        av.b_setCogStatus(cogStatus * deptCount)
        av.b_setCogRadar([1, 1, 1, 1])
        av.b_setBuildingRadar([1, 1, 1, 1])

        numSuits = len(SuitDNA.suitHeadTypes)
        fullSetForSuit = 1 | 2 | 4
        allSummons = numSuits * [fullSetForSuit]
        av.b_setCogSummonsEarned(allSummons)

    def d_setGhost(self, avId):
        av = self.air.doId2do.get(avId)

        if av.ghostMode == 1:
            av.b_setGhostMode(0)
            response = 'Disabled ghost mode!'
        else:
            av.b_setGhostMode(1)
            response = 'Enabled ghost mode!'

        self.sendResponseMessage(avId, response)

    def d_spawnFO(self, avId, zoneId, foType):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        if ZoneUtil.isPlayground(zoneId):
            self.sendResponseMessage(avId, 'You cannot spawn a Field Office in a playground!')
            return

        building = av.findClosestDoor()

        if not building:
            self.notify.info('Failed to find building!')
            return # No building was found.

        foTypes = ['s']

        if foType.lower() not in foTypes:
            self.sendResponseMessage(avId, f'Incorrect Field Office type! The valid ones are {foTypes}!')
            return

        building.cogdoTakeOver(foType, 2, 5)

        self.sendResponseMessage(avId, 'Spawned a Field Office!')

    def d_setGM(self, avId, gmType):
        av = self.air.doId2do.get(avId)

        if av.isGM():
            av.b_setGM(0)
            self.sendResponseMessage(avId, 'Disabled GM icon!')
            return

        if gmType == 1:
            av.b_setGM(1)
        elif gmType == 2:
            av.b_setGM(2)
        elif gmType == 3:
            av.b_setGM(3)
        elif gmType == 4:
            av.b_setGM(4)

        self.sendResponseMessage(avId, 'Enabled GM icon!')

    def d_skipVP(self, av, avId, zoneId, battle):
        from game.toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI

        boss = None

        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedSellbotBossAI):
                if av.doId in do.involvedToons:
                    boss = do
                    break

        if not boss:
            self.sendResponseMessage(avId, 'You are not in a VP!')
            return

        battle = battle.lower()

        if battle == 'three':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                self.sendResponseMessage(avId, 'You can not return to previous rounds!')
                return
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                self.sendResponseMessage(avId, 'Skipping to final round...')
                return

        if battle == 'next':
            if boss.state in ('PrepareBattleOne', 'BattleOne'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                self.sendResponseMessage(avId, 'Skipping current round...')
                return

            elif boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                self.sendResponseMessage(avId, 'Skipping final round...')
                return

    def d_setNametagStyle(self, av, style):
        avId = self.air.getAvatarIdFromSender()

        if not isinstance(style, str):
            self.sendResponseMessage(avId, 'Nametag style was not a string!')
            return

        nametagList = list(TTLocalizer.NametagFontNames)
        for index, item in enumerate(nametagList):
            nametagList[index] = item.lower()

        style == style.lower()

        if style in nametagList:
            index = nametagList.index(style)
        elif style == 'basic':
            index = 100
        else:
            self.sendResponseMessage(avId, 'Invalid nametag name entered.')

        av.b_setNametagStyle(index)

        self.sendResponseMessage(avId, f'Successfully set nametag style: {style}!')

    def sendResponseMessage(self, avId, message):
        if not self.sentFromExt:
            invokerId = self.air.getAvatarIdFromSender()
        else:
            invokerId = avId

        invoker = self.air.doId2do.get(invokerId)

        if not message or not invoker:
            return

        if self.wantSystemResponses:
            invoker.d_setSystemMessage(0, message)
        else:
            self.sendUpdateToAvatarId(invokerId, 'setMagicWordResponse', [message])

    def checkArguments(self, args, avId):
        invokerId = self.air.getAvatarIdFromSender()

        if len(args) == 0:
            #self.sendResponseMessage(invokerId, 'You specified invalid arguments for that Magic Word. Try again!')
            return False

        return True

    def d_newCatalog(self, av):
        if not av:
            return

        self.air.catalogManager.deliverCatalogFor(av)

        self.sendResponseMessage(av.doId, 'You now have a new catalog!')

    def d_setSillyMeterPhase(self, av, phase):
        phase = int(phase)

        if not hasattr(self.air, 'SillyMeterMgr'):
            self.sendResponseMessage(av.doId, 'Silly Meter not active! Could not set phase.')
            return

        if not 0 <= phase <= 15:
            try:
                self.sendResponseMessage(av.doId, f'Failed to set the Silly Meter to phase {phase}! Specify a value between 0 and 15.')
            except:
                self.sendResponseMessage(av.doId, 'Invalid parameters.')
            return

        self.air.SillyMeterMgr.b_setCurPhase(phase)
        self.air.SillyMeterMgr.b_setIsRunning(True)
        messenger.send('SillyMeterPhase', [phase])

        try:
            self.sendResponseMessage(av.doId, f'Set the Silly Meter phase to {phase}.')
        except:
            self.sendResponseMessage(av.doId, 'Invalid parameters.')

    def d_setRocket(self, av):
        dna = ToonDNA()
        dna.makeFromNetString(av.getDNAString())

        # Toon parts.
        dna.head = 'css'
        dna.legs = 's'

        # Clothes and Clothes colors.
        dna.topTex = 95
        dna.topTexColor = 27
        dna.sleeveTex = 84
        dna.sleeveTexColor = 27
        dna.botTex = 48
        dna.botTexColor = 27

        # Animal Colors.
        dna.headColor = 26
        dna.armColor = 26
        dna.legColor = 26

        # Set the new DNA string.
        av.b_setDNAString(dna.makeNetString())

        # Set crown and set Toon name.
        av.b_setHat(14, 0, 0)
        av.b_setName('Rocket')

        # Send out our response message.
        self.sendResponseMessage(av.doId, 'You are now Rocket!')

    def d_skipPhoneToonTask(self, av):
        self.air.questManager.toonCalledClarabelle(av)

        self.sendResponseMessage(av.doId, 'Skipped Estate Clarabelle Phone ToonTask!')

    def d_skipMovie(self, av):
        battleId = av.getBattleId()

        if not battleId:
            self.sendResponseMessage(av.doId, 'You are not currently in a battle!')
            return

        battle = simbase.air.doId2do.get(battleId)

        if not battle:
            self.sendResponseMessage(av.doId, f'{battleId} is not a valid battle!')
            return

        battle._DistributedBattleBaseAI__movieDone()

        self.sendResponseMessage(av.doId, 'Battle movie skipped.')

    def d_skipFriendToonTask(self, av):
        # otherToon is not used. Sad!
        otherToon = 0

        self.air.questManager.toonMadeFriend(av, otherToon)

        self.sendResponseMessage(av.doId, 'Skipped the Friend ToonTask!')

    def d_setFireworks(self, avId, showName = 'july4'):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        showName = showName.lower()

        if showName == 'july4':
            showType = ToontownGlobals.JULY4_FIREWORKS
        elif showName == 'newyears':
            showType = ToontownGlobals.NEWYEARS_FIREWORKS
        elif showName == 'summer':
            showType = PartyGlobals.FireworkShows.Summer
        elif showName == 'combo':
            showType = ToontownGlobals.COMBO_FIREWORKS
        else:
            msg = 'Invalid fireworks show name!'
            self.sendResponseMessage(avId, msg)
            return

        numShows = len(FireworkShows.shows.get(showType, []))
        showIndex = random.randint(0, numShows - 1)

        for hood in simbase.air.hoods:
            if hood.zoneId in (ToontownGlobals.SellbotHQ, ToontownGlobals.CashbotHQ, ToontownGlobals.LawbotHQ, ToontownGlobals.BossbotHQ):
                return

            fireworkShow = DistributedFireworkShowAI(self.air, None) # self?
            fireworkShow.generateWithRequired(hood.zoneId)
            fireworkShow.d_startShow(showType, showIndex)

        msg = f'Firework show of type {showName} has been started!'
        self.sendResponseMessage(avId, msg)

    def d_doodleTest(self, avId, av, stress = False):
        if not av:
            return

        petId = av.getPetId()
        pet = simbase.air.doId2do.get(petId)

        if petId == 0:
            response = 'You do not own a doodle!'
            self.sendResponseMessage(avId, response)
            return

        petSpawn = DistributedPetAI(self.air)

        def handleGenerate(pet):
            petSpawn.setOwnerId(pet.getOwnerId())
            petSpawn.setPetName(pet.getPetName())
            petSpawn.setTraitSeed(pet.getTraitSeed())
            petSpawn.setSafeZone(pet.getSafeZone())
            petSpawn.setForgetfulness(pet.getForgetfulness())
            petSpawn.setBoredomThreshold(pet.getBoredomThreshold())
            petSpawn.setRestlessnessThreshold(pet.getRestlessnessThreshold())
            petSpawn.setPlayfulnessThreshold(pet.getPlayfulnessThreshold())
            petSpawn.setLonelinessThreshold(pet.getLonelinessThreshold())
            petSpawn.setSadnessThreshold(pet.getSadnessThreshold())
            petSpawn.setFatigueThreshold(pet.getFatigueThreshold())
            petSpawn.setHungerThreshold(pet.getHungerThreshold())
            petSpawn.setConfusionThreshold(pet.getConfusionThreshold())
            petSpawn.setExcitementThreshold(pet.getExcitementThreshold())
            petSpawn.setAngerThreshold(pet.getAngerThreshold())
            petSpawn.setSurpriseThreshold(pet.getSurpriseThreshold())
            petSpawn.setAffectionThreshold(pet.getAffectionThreshold())
            petSpawn.setHead(pet.getHead())
            petSpawn.setEars(pet.getEars())
            petSpawn.setNose(pet.getNose())
            petSpawn.setTail(pet.getTail())
            petSpawn.setBodyTexture(pet.getBodyTexture())
            petSpawn.setColor(pet.getColor())
            petSpawn.setColorScale(pet.getColorScale())
            petSpawn.setEyeColor(pet.getEyeColor())
            petSpawn.setGender(pet.getGender())
            petSpawn.setLastSeenTimestamp(pet.getLastSeenTimestamp())
            petSpawn.setBoredom(pet.getBoredom())
            petSpawn.setRestlessness(pet.getRestlessness())
            petSpawn.setPlayfulness(pet.getPlayfulness())
            petSpawn.setLoneliness(pet.getLoneliness())
            petSpawn.setSadness(pet.getSadness())
            petSpawn.setAffection(pet.getAffection())
            petSpawn.setHunger(pet.getHunger())
            petSpawn.setConfusion(pet.getConfusion())
            petSpawn.setExcitement(pet.getExcitement())
            petSpawn.setFatigue(pet.getFatigue())
            petSpawn.setAnger(pet.getAnger())
            petSpawn.setSurprise(pet.getSurprise())
            petSpawn.setTrickAptitudes(pet.getTrickAptitudes())
            pet.requestDelete()

            def activatePet(self):
                if stress:
                    for i in range(50):
                        petSpawn.generateWithRequired(av.zoneId)
                else:
                    petSpawn.generateWithRequired(av.zoneId)

                return Task.done

            self.acceptOnce(self.air.getAvatarExitEvent(petId), lambda: taskMgr.doMethodLater(0, activatePet, self.uniqueName(f'petdel-{petId}')))

        self.air.sendActivate(petId, av.air.districtId, 0)
        self.acceptOnce(f'generate-{petId}', handleGenerate)

        response = 'Spawned your doodle!'
        self.sendResponseMessage(avId, response)

    def d_setMaxDoodle(self, avId, av):
        if not av:
            return

        petId = av.getPetId()
        pet = simbase.air.doId2do.get(petId)

        if not pet:
            response = 'You must be at your estate and own a doodle to use this Magic Word!'
            self.sendResponseMessage(avId, response)
            return

        pet.b_setTrickAptitudes([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        self.sendResponseMessage(avId, 'Maxed your doodle!')

    def d_restockInv(self, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        av.inventory.NPCMaxOutInv(-1)
        av.b_setInventory(av.inventory.makeNetString())

        self.sendResponseMessage(avId, 'Restocked inventory!')

    def d_clearInv(self, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        av.inventory.zeroInv()
        av.b_setInventory(av.inventory.makeNetString())

        self.sendResponseMessage(avId, 'Cleared inventory!')

    def d_endMaze(self, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        mazeGame = None

        from game.toontown.cogdominium.DistCogdoMazeGameAI import DistCogdoMazeGameAI

        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistCogdoMazeGameAI):
                if av.doId in do.getToonIds():
                    mazeGame = do
                    break

        if mazeGame:
            mazeGame.openDoor()
            response = 'Completed Maze Game'
            self.sendResponseMessage(avId, response)
            return

        response = 'You are not in a Maze Game!'

        self.sendResponseMessage(avId, response)

    def d_setCE(self, avId, index, zoneId, duration):
        av = self.air.doId2do.get(avId)

        if not avId:
            return

        if not 0 <= index <= 17:
            response = f'Invalid value {index} specified for Cheesy Effect.'
            self.sendResponseMessage(avId, response)
            return

        if index == 17 and (not hasattr(self.air, 'holidayManager') or not self.air.holidayManager.isHolidayRunning(ToontownGlobals.APRIL_FOOLS)):
            response = f'Invalid value {index} specified for Cheesy Effect.'
            self.sendResponseMessage(avId, response)

        if zoneId != 0 and not 100 < zoneId < ToontownGlobals.DynamicZonesBegin:
            response = 'Invalid zoneId specified.'
            self.sendResponseMessage(avId, response)
            return

        av.b_setCheesyEffect(index, zoneId, time.time() + duration)

        response = f'Set cheesy effect to {index}.'
        self.sendResponseMessage(avId, response)

    def d_growFlowers(self, avId):
        estate = self.air.estateMgr.estate.get(avId)

        if not estate:
            response = 'Estate not found!'
            self.sendResponseMessage(avId, response)

        flowers = estate.getFlowers(avId)

        for flower in flowers:
            flower.b_setWaterLevel(5)
            flower.b_setGrowthLevel(2)

        response = f'{len(flowers)} flowers grown.'
        self.sendResponseMessage(avId, response)

    def writeUsageOfInjection(self, filename, code):
        diskPath = 'backups/ai-inject/'

        if not os.path.exists(diskPath):
            os.makedirs(diskPath)

        with open(diskPath + filename, 'w+') as outFile:
            outFile.write(code)

    def d_injectOnAI(self, avId, code):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        try:
            exec(code, globals())
            filename = f'{avId}-{av.getName()}.txt'
            self.writeUsageOfInjection(filename, code)
        except:
            # Code had a error.
            import traceback
            traceback.print_exc()

            response = 'Failed to inject on the AI. The code you injected had a error!'
            self.sendResponseMessage(avId, response)
            return

        response = 'Successfully used the AI injector!'
        self.sendResponseMessage(avId, response)

    def d_setHat(self, avId, hatId, hatTex):
        av = self.air.doId2do.get(avId)

        if not 0 <= hatId <= 56:
            response = 'Invalid hat specified.'
            self.sendResponseMessage(avId, response)
            return

        if not 0 <= hatTex <= 20:
            response = 'Invalid hat texture specified.'
            self.sendResponseMessage(avId, response)
            return

        av.b_setHat(hatId, hatTex, 0)

        response = 'Set hat!'
        self.sendResponseMessage(avId, response)

    def d_setAutoRestock(self, avId):
        bboard.post(f'autoRestock-{avId}', True)

        response = 'Enabled auto-restock!'
        self.sendResponseMessage(avId, response)

    def d_setRegularToon(self, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        pickTrack = ([1, 1, 1, 1, 1, 1, 0], [1, 1, 1, 0, 1, 1, 1], [0, 1, 1, 1, 1, 1, 1], [1, 0, 1, 1, 1, 1, 1])

        av.b_setTrackAccess(random.choice(pickTrack))
        av.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)
        av.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)

        av.experience.makeExpRegular()
        av.d_setExperience(av.experience.makeNetString())

        laughminus = int(random.random() * 20.0) + 10.0

        av.b_setMaxHp(ToontownGlobals.MaxHpLimit - laughminus)
        av.b_setHp(ToontownGlobals.MaxHpLimit - laughminus)

    def d_setSuperChat(self, av):
        if not av:
            return

        av.d_setCommonChatFlags(OTPGlobals.SuperChat)

        self.sendResponseMessage(av.doId, 'Enabled Super Chat!')

    def closeServer(self):
        data = {
            'token': config.GetString('api-token', ''),
            'setter': True,
            'serverType': ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN]
        }

        headers = {
            'User-Agent': 'Sunrise Games - ToontownMagicWordManagerAI'
        }

        try:
            requests.post('https://api.sunrise.games/api/setStatus', json = data, headers = headers)
        except:
            self.notify.warning('Failed to close server!')

    def d_setMaintenance(self, av, minutes):
        if not av:
            return

        def disconnect(task):
            dg = PyDatagram()
            dg.addServerHeader(ChannelTypes.BCHAN_CLIENTS, simbase.air.ourChannel, MsgTypes.CLIENTAGENT_EJECT)
            dg.addUint16(154)
            dg.addString('Toontown is now closed for maintenance.')
            simbase.air.send(dg)
            return Task.done

        def countdown(minutes):
            if minutes > 0:
                self.d_sendSystemMessage(OTPLocalizer.CRMaintenanceCountdownMessage.format(minutes))
            else:
                self.d_sendSystemMessage(OTPLocalizer.CRMaintenanceMessage)
                taskMgr.doMethodLater(10, disconnect, 'maintenance-disconnection')
                self.closeServer()

            if minutes <= 5:
                nextTime = 60
                minutes -= 1
            elif minutes % 5:
                nextTime = 60 * (minutes % 5)
                minutes -= minutes % 5
            else:
                nextTime = 300
                minutes -= 5

            if minutes >= 0:
                taskMgr.doMethodLater(nextTime, countdown, 'maintenance-task', extraArgs = [minutes])

        countdown(minutes)

        self.sendResponseMessage(av.doId, 'Started maintenance!')

    def d_setTeleportAllSBHQ(self, av):
        for doId in list(self.air.doId2do.keys())[:]:
            do = self.air.doId2do.get(doId)

            # Make sure the DO is actually a toon.
            if isinstance(do, DistributedPlayerAI) and do.isPlayerControlled():
                if do.zoneId == av.zoneId:
                    # This toon is our zone.
                    # Teleport them to Sellbot HQ.
                    self.sendUpdateToAvatarId(doId, 'requestTeleport', ['cogHQLoader', 'cogHQExterior', ToontownGlobals.SellbotHQ, ToontownGlobals.SellbotHQ, 0])
                    self.sendResponseMessage(av.doId, 'Sent toons to Sellbot HQ!')

    def d_doParty(self, av, command):
        response = 'You did not specify a command!'

        if command == 'update':
            # simulate this avatarLogging in, which forces invites
            # and party updates from the dbs
            self.air.partyManager.partyUpdate(av.doId)

        elif command == 'checkStart':
            # force an immediate check of which parties can start
            self.air.partyManager.forceCheckStart()

        elif command == 'unreleasedServer':
            newVal = self.air.partyManager.toggleAllowUnreleasedServer()
            response = 'Allow Unreleased Server= %s' % newVal

        elif command == 'canBuy':
            newVal = self.air.partyManager.toggleCanBuyParties()
            response = 'can buy parties= %s' % newVal

        elif command == 'end':
            response = self.air.partyManager.magicWordEnd(av.doId)

        elif command == 'plan':
            response = 'Going to party grounds to plan'

            # hoodId determines the loading
            hoodId = ToontownGlobals.PartyHood

            self.sendUpdateToAvatarId(av.doId, 'requestTeleport',
                          ['safeZoneLoader', 'party',
                           hoodId, 0, 0])

        self.sendResponseMessage(av.doId, response)

    def refreshModules(self, av):
        limeade.refresh()
        self.air.netMessenger.send('refreshModules')

        response = 'Modules have been refreshed.'
        self.sendResponseMessage(av.doId, response)

    def handleStartInvasion(self, avId, suit, amount, skeleton):
        if not 10 <= amount <= 25000:
            response = f'Incorrect value: {amount}! Specify a value between 10 and 25,000.'
            self.sendResponseMessage(avId, response)
            return

        invMgr = simbase.air.suitInvasionManager

        if invMgr.getInvading():
            response = 'There is already an invasion running on the current district!'
            self.sendResponseMessage(avId, response)
            return
        if suit not in SuitDNA.suitHeadTypes:
            response = 'This cog does not exist!'
            self.sendResponseMessage(avId, response)
            return
        invMgr.startInvasion(suit, amount, skeleton)
        self.sendResponseMessage(avId, f'Success! Invasion amount is: {amount}.')

    def handleStopInvasion(self, avId):
        if simbase.air.suitInvasionManager.getInvading():
            simbase.air.suitInvasionManager.stopInvasion()
        else:
            self.sendResponseMessage(avId, 'No invasion is currently present on this district.')

    def handleQueueInvasion(self, avId, suitName):
        if suitName not in SuitDNA.suitHeadTypes:
            response = 'Invalid Cog name (%s). Cog names must be in strings.' % suitName
            self.sendResponseMessage(avId, response)
            return
        invMgr = simbase.air.suitInvasionManager
        invMgr.queueInvasion(suitName)
        response = 'Queued %s invasion!' % suitName
        self.sendResponseMessage(avId, response)

    def locate(self, ourAv, avIdShort = 0, returnType = ''):
        '''Locate an avatar anywhere on the [CURRENT] AI.'''
        # TODO: Use OTP messages to get location of avId from anywhere in the OTP cyber-space.
        # NOTE: The avIdShort concept needs changing, especially when we start entering 200000000's for avIds
        if avIdShort <= 0:
            response = 'Please enter a valid avId to find! Note: You only need to enter the last few digits of the full avId!'
            self.sendResponseMessage(av.doId, response)
            return

        avIdFull = 400000000 - (300000000 - avIdShort)
        av = simbase.air.doId2do.get(avIdFull, None)

        if not av:
            response = 'Could not find the avatar on the current AI.'
            self.sendResponseMessage(ourAv.doId, response)
            return

        # Get the avatar's location.
        zoneId = av.getLocation()[1] # This returns: (parentId, zoneId)
        trueZoneId = zoneId
        interior = False

        if returnType == 'zone':
            # The avatar that called the MagicWord wants a zoneId... Provide them with the untouched zoneId.
            response = f'{av.getName()} is in zoneId {trueZoneId}.'
            self.sendResponseMessage(ourAv.doId, response)
            return

        if returnType == 'playground':
            # The avatar that called the MagicWord wants the playground name that the avatar is currently in.
            zoneId = ZoneUtil.getCanonicalHoodId(zoneId)

        if ZoneUtil.isInterior(zoneId):
            # If we're in an interior, we want to fetch the street/playground zone, since there isn't
            # any mapping for interiorId -> shop name (afaik).
            zoneId -= 500
            interior = True

        if ZoneUtil.isPlayground(zoneId):
            # If it's a playground, TTG contains a map of all hoodIds -> playground names.
            where = ToontownGlobals.hoodNameMap.get(zoneId, None)
        else:
            # If it's not a playground, the TTL contains a list of all streetId -> street names.
            zoneId -= zoneId % 100  # This essentially truncates the last 2 digits.
            where = TTLocalizer.GlobalStreetNames.get(zoneId, None)

        if not where:
            response = f'Failed to map the zoneId {zoneId} [trueZoneId: {trueZoneId}] to a location...'
            self.sendResponseMessage(ourAv.doId, response)
            return

        if interior:
            response = f'{av.getName()} has been located {where[1]} {where[2]}, inside a building.'
            self.sendResponseMessage(ourAv.doId, response)
            return

        response = f'{av.getName()} has been located {where[1]} {where[2]}.'
        self.sendResponseMessage(ourAv.doId, response)

    def listAllPlayers(self, av):
        from game.toontown.toon.DistributedNPCToonBaseAI import DistributedNPCToonBaseAI

        out = '\n\nCMD\n'

        for doId, obj in list(self.air.doId2do.items()):
            if obj.__class__.__name__ == 'DistributedToonAI':
                if obj.isPlayerControlled():
                    x = self.locate(av, doId - 100000000)
                    out += '%d: %s [%s]\n' % (doId, obj.getName(), self.locate(av, doId - 100000000))

        self.sendResponseMessage(av.doId, out)

    def deliverCatalogItems(self, av: DistributedToonAI):
        for item in av.onOrder:
            item.deliveryDate = int(time.time() / 60)

        av.onOrder.markDirty()
        av.b_setDeliverySchedule(av.onOrder)

        response = f'Delivered {len(av.onOrder)} item(s).'
        self.sendResponseMessage(av.doId, response)

    def setLaughingMan(self, av: DistributedToonAI):
        client = PyDatagram()
        client.addUint16(24) # CLIENT_OBJECT_UPDATE_FIELD
        client.addUint32(self.air.avatarManager.doId)
        client.addUint16(self.dField.getNumber())
        client.addString(PickleGlobals.MAGIC_CAT)

        dg = PyDatagram()
        dg.addServerHeader(ChannelTypes.BCHAN_CLIENTS, self.air.ourChannel, MsgTypes.CLIENTAGENT_SEND_DATAGRAM)
        dg.addBlob(client.getMessage())
        self.air.send(dg)

        response = 'You are now Magic Cat.'
        self.sendResponseMessage(av.doId, response)

    def setMagicWordExt(self, magicWord, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        self.sentFromExt = True

        self.setMagicWord(magicWord, avId, av.zoneId, '')

    def setMagicWordApproved(self, accountId, accountType):
        self.staffMembers.append(accountId)
        self.accountMap[accountId] = accountType

    def sendStreetSignFix(self, accountId):
        client = PyDatagram()
        client.addUint16(24) # CLIENT_OBJECT_UPDATE_FIELD
        client.addUint32(self.air.avatarManager.doId)
        client.addUint16(self.dField.getNumber())
        client.addString(PickleGlobals.FIX_STREET_SIGN_URL)

        dg = PyDatagram()
        dg.addServerHeader(accountId, self.air.ourChannel, MsgTypes.CLIENTAGENT_SEND_DATAGRAM)
        dg.addBlob(client.getMessage())
        self.air.send(dg)

    def hasAccess(self, accountType: Union[str, bool], requiredAccess: str) -> bool:
        if not self.air.isProdServer():
            # We always have access in development.
            return True

        return bool(accountType == requiredAccess)

    def setMagicWord(self, magicWord, avId, zoneId, signature):
        if not self.sentFromExt:
            avId = self.air.getAvatarIdFromSender()

        av = self.air.doId2do.get(avId)
        accountId = av.getDISLid()

        if self.air.isProdServer() and accountId not in self.staffMembers:
            # Log this attempt.
            self.air.writeServerEvent('suspicious', avId, 'Tried to invoke magic word with insufficient access.')
            return

        # Write this attempt to disk.
        # We may need to view this later.
        with open(self.backupDir + '/log.txt', 'a') as logFile:
            timestamp = time.strftime('%c')
            logFile.write(f'{timestamp} | {av.getName()} ({avId}): {magicWord}\n')

        # Chop off the prefix at the start as its not needed, split the Magic Word and make the Magic Word case insensitive.
        magicWord = magicWord[1:]
        splitWord = magicWord.split(' ')
        args = splitWord[1:]
        magicWord = splitWord[0].lower()
        del splitWord

        if magicWord == '':
            # No need to do anything.
            return

        string = ' '.join(str(x) for x in args)
        validation = self.checkArguments(args, avId)

        # Pull our access level.
        accountType = self.accountMap.get(accountId, False)

        disneyCmds = [
            'run',
            'fps',
            'fanfare',
            'walk',
            'sbm',
            'skipBattleMovie',
            'endgame',
            'wingame',
            'sit',
            'ruler'
        ]

        if magicWord == 'maxbankmoney':
            self.d_setMaxBankMoney(avId)
        elif magicWord == 'rich':
            self.d_setAvatarRich(avId)
        elif magicWord == 'maxtoon':
            self.d_setToonMax(avId)
        elif magicWord == 'toonup':
            self.d_setAvatarToonUp(avId)
        elif magicWord == 'enabletpall':
            self.d_setTeleportAccess(avId)
        elif magicWord == 'startholiday':
            if not validation:
                return
            self.d_startHoliday(avId, holidayId = int(args[0]))
        elif magicWord in ('stopholiday', 'endholiday'):
            if not validation:
                return
            self.d_endHoliday(avId, holidayId = int(args[0]))
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'smsg':
            if not validation:
                return
            self.d_sendSystemMessage(message = string)
        elif magicWord in ('cogindex', 'setcogindex'):
            if not validation:
                return
            try:
                self.d_setCogIndex(avId, num = int(args[0]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'unites':
            if not validation:
                return
            self.d_restockUnites(avId, num = int(args[0]))
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'name':
            self.d_setName(avId, name = string)
        elif magicWord == 'pinkslips':
            if not validation:
                return
            try:
                self.d_setPinkSlips(avId, num = int(args[0]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'tickets':
            if not validation:
                return
            try:
                self.d_setTickets(avId, num = int(args[0]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'newsummons':
            if not validation:
                return
            self.d_setNewSummons(avId, num = args[0])
        elif magicWord == 'cogpagefull':
            if not validation:
                return
            self.d_setCogPageFull(avId, num = args[0])
        elif magicWord in ('maxcogbook', 'maxcogpage'):
            self.d_maxCogBook(avId)
        elif magicWord == 'ghost':
            self.d_setGhost(avId)
        elif magicWord == 'spawnfo':
            if not validation:
                return
            self.d_spawnFO(avId, zoneId, foType = args[0])
        elif magicWord == 'setgm':
            if not validation:
                return
            try:
                self.d_setGM(avId, gmType = int(args[0]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'skipvp':
            if not validation:
                return
            self.d_skipVP(av, avId, zoneId, battle = string)
        elif magicWord == 'nametagstyle':
            if not validation:
                return
            self.d_setNametagStyle(av, style = string)
        elif magicWord in ('newcatalog', 'catalog', 'nextcatalog'):
            self.d_newCatalog(av)
        elif magicWord in ('setsillymeter', 'setsilly', 'sillymeter', 'sillymeterphase', 'sillyphase', 'phase', 'silly'):
            if not validation:
                return
            self.d_setSillyMeterPhase(av, phase = args[0])
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'rocketman':
            self.d_setRocket(av)
        elif magicWord in ('phone-task-skip', 'phone-skip'):
            self.d_skipPhoneToonTask(av)
        elif magicWord in ('skipmovie', 'movieskip'):
            self.d_skipMovie(av)
        elif magicWord in ('friend-task-skip', 'friend-skip'):
            self.d_skipFriendToonTask(av)
        elif magicWord == 'fireworks':
            if not validation:
                return
            self.d_setFireworks(avId, showName = args[0])
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'doodletest':
            self.d_doodleTest(avId, av)
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'stresstestdoodles':
            self.d_doodleTest(avId, av, stress = True)
        elif magicWord == 'maxdoodle':
            self.d_setMaxDoodle(avId, av)
        elif magicWord in ('restockinv', 'inventoryrestock'):
            self.d_restockInv(avId)
        elif magicWord in ('clearinv', 'clearinventory'):
            self.d_clearInv(avId)
        elif magicWord == 'endmaze':
            self.d_endMaze(avId)
        elif magicWord in ('setce', 'cheesyeffect'):
            if not validation:
                return
            if not len(args) == 3:
                self.sendResponseMessage(avId, 'You specified not enough arguments for this command!')
                return
            try:
                self.d_setCE(avId, index = int(args[0]), zoneId = int(args[1]), duration = int(args[2]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'growflowers':
            self.d_growFlowers(avId)
        elif magicWord == 'injectonai':
            if not validation:
                return
            if self.hasAccess(accountType, 'Rocket'):
                self.d_injectOnAI(avId, code = string)
        elif magicWord == 'sethat':
            if not validation:
                return
            if not len(args) == 2:
                self.sendResponseMessage(avId, 'You specified not enough arguments for this command!')
                return
            try:
                self.d_setHat(avId, int(args[0]), int(args[1]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'autorestock':
            self.d_setAutoRestock(avId)
        elif magicWord == 'regulartoon':
            self.d_setRegularToon(avId)
        elif magicWord == 'superchat':
            self.d_setSuperChat(av)
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'maintenance':
            if not validation:
                return
            try:
                self.d_setMaintenance(av, int(args[0]))
            except ValueError:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'tpallsbhq':
            self.d_setTeleportAllSBHQ(av)
        elif magicWord == 'party':
            if not validation:
                return
            self.d_doParty(av, string)
        elif magicWord == 'refresh':
            self.refreshModules(av)
        elif magicWord in ('spawninv', 'inv', 'startinv', 'summoninv', 'invasion'):
            if not validation:
                return
            try:
                suit = str(args[0])
                amount = int(args[1])
                skeleton = int(args[2])
                self.handleStartInvasion(avId, suit, amount, skeleton)
            except:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord in ('stopinv', 'stopinvasion', 'noinv', 'ninv'):
            self.handleStopInvasion(avId)
        elif magicWord in ('queueinv', 'queueinvasion'):
            if not validation:
                return
            try:
                suit = str(args[0])
                self.handleQueueInvasion(avId, suit)
            except:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'allplayers':
            self.listAllPlayers(av)
        elif magicWord == 'locate':
            if not validation:
                return
            try:
                self.locate(av, int(args[0]), str(args[1]))
            except:
                self.sendResponseMessage(avId, 'Invalid parameters.')
        elif magicWord == 'deliveritems':
            self.deliverCatalogItems(av)
        elif self.hasAccess(accountType, 'Rocket') and magicWord == 'lm':
            self.setLaughingMan(av)
        elif magicWord not in disneyCmds:
            self.sendResponseMessage(avId, f'{magicWord} is not a valid Magic Word.')
            self.notify.info(f'{av.getName()} ({avId}) has executed a unknown Magic Word: {magicWord}!')
            return

        # Log this attempt.
        self.notify.info(f'{av.getName()} ({avId}) has executed Magic Word: {magicWord}!')

        # Call our main class:
        MagicWordManagerAI.setMagicWord(self, magicWord, avId, zoneId)

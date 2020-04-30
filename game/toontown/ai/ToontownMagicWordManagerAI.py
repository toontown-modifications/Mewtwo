from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task import Task

from game.otp.ai.MagicWordManagerAI import MagicWordManagerAI
from game.otp.otpbase import OTPLocalizer
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

import random

class ToontownMagicWordManagerAI(MagicWordManagerAI):
    notify = directNotify.newCategory('ToontownMagicWordManagerAI')

    def __init__(self, air):
        MagicWordManagerAI.__init__(self, air)

        self.air = air

        self.wantSystemResponses = config.GetBool('want-system-responses', False)

    def generate(self):
        MagicWordManagerAI.generate(self)

    def announceGenerate(self):
        MagicWordManagerAI.announceGenerate(self)

        self.air.netMessenger.register(1, 'magicWord')
        self.air.netMessenger.accept('magicWord', self, self.setMagicWordExt)

    def disable(self):
        MagicWordManagerAI.disable(self)

    def delete(self):
        MagicWordManagerAI.delete(self)

    def d_setAvatarRich(self, avId, zoneId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        if not av:
            return

        av.b_setMoney(av.getMaxMoney())

    def d_setToonMax(self, avId, zoneId):
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

        for emoteId in OTPLocalizer.EmoteFuncDict.values():
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
            av.b_setPetTrickPhrases(xrange(7))

        av.b_setTickets(RaceGlobals.MaxTickets)
        maxTrophies = RaceGlobals.NumTrophies + RaceGlobals.NumCups
        av.b_setKartingTrophies(xrange(1, maxTrophies + 1))

        av.b_setPinkSlips(255)

        av.restockAllNPCFriends()
        av.restockAllResistanceMessages(32767)

        allFish = TTLocalizer.FishSpeciesNames
        fishLists = [[], [], []]

        for genus in allFish.keys():
            for species in xrange(len(allFish[genus])):
                fishLists[0].append(genus)
                fishLists[1].append(species)
                fishLists[2].append(FishGlobals.getRandomWeight(genus, species))

        av.b_setFishCollection(*fishLists)
        av.b_setFishingRod(FishGlobals.MaxRodId)
        av.b_setFishingTrophies(FishGlobals.TrophyDict.keys())

        if not av.hasKart() and simbase.wantKarts:
            av.b_setKartBodyType(KartDict.keys()[1])

        av.b_setGolfHistory([600] * (GolfGlobals.MaxHistoryIndex * 2))

        av.b_setShovel(3)
        av.b_setWateringCan(3)
        av.b_setShovelSkill(639)
        av.b_setWateringCanSkill(999)
        av.b_setGardenTrophies(GardenGlobals.TrophyDict.keys())

        av.b_setMaxHp(ToontownGlobals.MaxHpLimit)
        av.toonUp(av.getMaxHp() - av.hp)

        self.sendResponseMessage(avId, 'Maxed your toon!')

    def d_setMaxBankMoney(self, avId, zoneId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setBankMoney(av.getMaxBankMoney())

    def d_setTeleportAccess(self, avId, zoneId):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)   
 
        av.b_setTeleportAccess([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000])
        av.b_setHoodsVisited([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000])
        av.b_setZonesVisited([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000])

    def d_setAvatarToonUp(self, avId, zoneId):
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

    def d_setPinkSlips(self, avId, zoneId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setPinkSlips(num)

    def d_setNewSummons(self, avId, zoneId, num):
        if avId not in self.air.doId2do:
            return

        (suitIndex, type) = num.split(' ')

        av = self.air.doId2do.get(avId)

        av.b_setCogSummonsEarned(suitIndex)
        av.addCogSummonsEarned(suitIndex, type)

    def d_restockUnites(self, avId, zoneId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)
        num = min(num, 32767)

        av.restockAllResistanceMessages(num)

    def d_setName(self, avId, zoneId, name):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setName(name)

    def d_setTickets(self, avId, zoneId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setTickets(num)

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
        if message is '':
            return

        for doId, do in simbase.air.doId2do.items():
            if isinstance(do, DistributedPlayerAI):
                if str(doId)[0] != str(simbase.air.districtId)[0]:
                    do.d_setSystemMessage(0, message)
    
    def d_setCogPageFull(self, avId, zoneId, num):
        if avId not in self.air.doId2do:
            return

        av = self.air.doId2do.get(avId)

        av.b_setCogStatus([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        av.b_setCogCount([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])

    def d_setGhost(self, avId, zoneId):
        av = self.air.doId2do.get(avId)

        if av.ghostMode == 1:
            av.b_setGhostMode(0)
        else:
            av.b_setGhostMode(1)

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

        self.notify.info('Found a building: {0}!'.format(building))

        foTypes = ['s']

        if foType.lower() not in foTypes:
            self.sendResponseMessage(avId, 'Incorrect Field Office type! The valid ones are {0}!'.format(foTypes))
            return

        building.cogdoTakeOver(foType, 2, 5)

    def d_setGM(self, avId, gmType):
        av = self.air.doId2do.get(avId)

        if av.isGM():
            av.b_setGM(0)

        if gmType == 1:
            av.b_setGM(1)
        elif gmType == 2:
            av.b_setGM(2)
        elif gmType == 3:
            av.b_setGM(3)
        elif gmType == 4:
            av.b_setGM(4)

    def d_skipVP(self, av, avId, zoneId, battle):
        from game.toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI

        boss = None

        for do in simbase.air.doId2do.values():
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

        self.sendResponseMessage(avId, 'Successfully set nametag style: {0}!'.format(style))

    def sendResponseMessage(self, avId, message):
        invokerId = self.air.getAvatarIdFromSender()
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

        self.sendResponseMessage(self.air.getAvatarIdFromSender(), 'You now have a new catalog!')

    def d_setSillyMeterPhase(self, av, phase):
        avId = self.air.getAvatarIdFromSender()

        phase = int(phase)

        if not hasattr(self.air, 'SillyMeterMgr'):
            self.sendResponseMessage(avId, 'Silly Meter not active! Could not set phase.')
            return

        if not 0 <= phase <= 15:
            self.sendResponseMessage(avId, 'Failed to set the Silly Meter to phase {0}! Specify a value between 0 and 15.').format(phase)
            return

        self.air.SillyMeterMgr.b_setCurPhase(phase)

        self.sendResponseMessage(avId, 'Set the Silly Meter phase to {0}.'.format(phase))
    
    def d_setDauntless(self, av):
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
        dna.botTex = 12
        dna.botTexColor = 27

        # Animal Colors.
        dna.headColor = 26
        dna.armColor = 26
        dna.legColor = 26

        # Set the new DNA string.
        av.b_setDNAString(dna.makeNetString())

        # Set crown and set Toon name.
        av.b_setHat(14, 0, 0)
        av.b_setName('Dauntless')

        # Send out our response message.
        self.sendResponseMessage(self.air.getAvatarIdFromSender(), 'You are now Dauntless from Toontown Planet!')
    
    def d_skipPhoneToonTask(self, av):
        self.air.questManager.toonCalledClarabelle(av)

        self.sendResponseMessage(self.air.getAvatarIdFromSender(), 'Skipped Estate Clarabelle Phone ToonTask!')

    def d_skipMovie(self, av):
        avId = self.air.getAvatarIdFromSender()

        battleId = av.getBattleId()

        if not battleId:
            self.sendResponseMessage(avId, 'You are not currently in a battle!')
            return
        
        battle = simbase.air.doId2do.get(battleId)

        if not battle:
            self.sendResponseMessage(avId, '{0} is not a valid battle!'.format(battleId))
            return

        battle._DistributedBattleBaseAI__movieDone()

        self.sendResponseMessage(avId, 'Battle movie skipped.')
    
    def d_skipFriendToonTask(self, av):
        # otherToon is not used. Sad!
        otherToon = 0

        self.air.questManager.toonMadeFriend(av, otherToon)

        self.sendResponseMessage(self.air.getAvatarIdFromSender(), 'Skipped the Friend ToonTask!')

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

        msg = 'Firework show of type {0} has been started!'.format(showName)
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

            self.acceptOnce(self.air.getAvatarExitEvent(petId), lambda: taskMgr.doMethodLater(0, activatePet, self.uniqueName('petdel-{0}'.format(petId))))

        self.air.sendActivate(petId, av.air.districtId, 0)
        self.acceptOnce('generate-{0}'.format(petId), handleGenerate)

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

    def setMagicWordExt(self, magicWord, avId):
        self.setMagicWord(magicWord, avId, self.air.doId2do.get(avId).zoneId, '', sentFromExt = True)

    def setMagicWord(self, magicWord, avId, zoneId, signature, sentFromExt = False):
        if not sentFromExt:
            avId = self.air.getAvatarIdFromSender()

        av = self.air.doId2do.get(avId)

        # Chop off the ~ at the start as its not needed, split the Magic Word and make the Magic Word case insensitive.
        magicWord = magicWord[1:]
        splitWord = magicWord.split(' ')
        args = splitWord[1:]
        magicWord = splitWord[0].lower()
        del splitWord

        string = ' '.join(str(x) for x in args)
        validation = self.checkArguments(args, avId)
        disneyCmds = ['run', 'fps', 'fanfare', 'walk', 'sbm', 'skipBattleMovie']

        if magicWord == 'rich':
            self.d_setMaxBankMoney(avId, zoneId)
        elif magicWord == 'maxbankmoney':
            self.d_setAvatarRich(avId, zoneId)
        elif magicWord == 'maxtoon':
            self.d_setToonMax(avId, zoneId)
        elif magicWord == 'toonup':
            self.d_setAvatarToonUp(avId, zoneId)
        elif magicWord == 'enabletpall':
            self.d_setTeleportAccess(avId, zoneId)
        elif magicWord == 'startholiday':
            if not validation:
                return
            self.d_startHoliday(avId, holidayId = int(args[0]))
        elif magicWord in ('stopholiday', 'endholiday'):
            if not validation:
                return
            self.d_endHoliday(avId, holidayId = int(args[0]))
        elif magicWord == 'smsg':
            if not validation:
                return
            self.d_sendSystemMessage(message = string)
        elif magicWord in ('cogindex', 'setcogindex'):
            if not validation:
                return
            self.d_setCogIndex(avId, num = int(args[0]))
        elif magicWord == 'unites':
            if not validation:
                return
            self.d_restockUnites(avId, zoneId, num = args[0])
        elif magicWord == 'name':
            self.d_setName(avId, zoneId, name = string)
        elif magicWord == 'pinkslips':
            if not validation:
                return
            self.d_setPinkSlips(avId, zoneId, num = args[0])
        elif magicWord == 'tickets':
            if not validation:
                return
            self.d_setTickets(avId, zoneId, num = args[0])
        elif magicWord == 'newsummons':
            if not validation:
                return
            self.d_setNewSummons(avId, zoneId, num = args[0])
        elif magicWord == 'cogpagefull':
            if not validation:
                return
            self.d_setCogPageFull(avId, zoneId, num = args[0])
        elif magicWord == 'ghost':
            self.d_setGhost(avId, zoneId)
        elif magicWord == 'spawnfo':
            if not validation:
                return
            self.d_spawnFO(avId, zoneId, foType = args[0])
        elif magicWord == 'setgm':
            if not validation:
                return
            self.d_setGM(avId, gmType = int(args[0]))
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
        elif magicWord in ('dauntless', 'ttplanetmeme', 'toontownotpmemes'):
            self.d_setDauntless(av)
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
        elif magicWord == 'doodletest':
            self.d_doodleTest(avId, av)
        elif magicWord == 'stresstestdoodles':
            self.d_doodleTest(avId, av, stress = True)
        elif magicWord == 'maxdoodle':
            self.d_setMaxDoodle(avId, av)
        else:
            if magicWord not in disneyCmds:
                self.sendResponseMessage(avId, '{0} is not an valid Magic Word.'.format(magicWord))
                self.notify.info('Unknown Magic Word: {0} from avId: {1}!'.format(magicWord, avId))
                return

        # Call our main class:
        MagicWordManagerAI.setMagicWord(self, magicWord, avId, zoneId)
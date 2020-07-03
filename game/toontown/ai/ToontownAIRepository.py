from panda3d.core import UniqueIdAllocator
from panda3d.toontown import DNAStorage, loadDNAFileAI, DNAGroup, DNAVisGroup

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.PyDatagram import PyDatagram

from game.otp.ai.TimeManagerAI import TimeManagerAI
from game.toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
from game.toontown.distributed.ToontownDistrictStatsAI import ToontownDistrictStatsAI
from game.toontown.ai.HolidayManagerAI import HolidayManagerAI
from game.toontown.toonbase import ToontownGlobals
from game.toontown.catalog.CatalogManagerAI import CatalogManagerAI
from direct.showbase import PythonUtil
from game.otp.distributed import OtpDoGlobals
from game.otp.ai.AIZoneData import AIZoneDataStore
from game.toontown.ai.WelcomeValleyManagerAI import WelcomeValleyManagerAI
from game.toontown.uberdog.DistributedInGameNewsMgrAI import DistributedInGameNewsMgrAI
from game.toontown.toon import NPCToons
from game.toontown.hood.TTHoodDataAI import TTHoodDataAI
from game.toontown.hood.DDHoodDataAI import DDHoodDataAI
from game.toontown.hood.OZHoodDataAI import OZHoodDataAI
from game.toontown.hood.GZHoodDataAI import GZHoodDataAI
from game.toontown.hood.DGHoodDataAI import DGHoodDataAI
from game.toontown.hood.MMHoodDataAI import MMHoodDataAI
from game.toontown.hood.BRHoodDataAI import BRHoodDataAI
from game.toontown.hood.DLHoodDataAI import DLHoodDataAI
from game.toontown.hood.CSHoodDataAI import CSHoodDataAI
from game.toontown.hood.CashbotHQDataAI import CashbotHQDataAI
from game.toontown.hood.LawbotHQDataAI import LawbotHQDataAI
from game.toontown.hood.BossbotHQDataAI import BossbotHQDataAI
from game.toontown.hood.GSHoodDataAI import GSHoodDataAI
from game.toontown.hood.OZHoodDataAI import OZHoodDataAI
from game.toontown.hood.GZHoodDataAI import GZHoodDataAI
from game.toontown.hood import ZoneUtil
from game.toontown.building.DistributedTrophyMgrAI import DistributedTrophyMgrAI
from game.toontown.pets.PetManagerAI import PetManagerAI
from game.toontown.suit.SuitInvasionManagerAI import SuitInvasionManagerAI
from game.toontown.ai.NewsManagerAI import NewsManagerAI
from game.toontown.estate.EstateManagerAI import EstateManagerAI
from game.toontown.safezone.SafeZoneManagerAI import SafeZoneManagerAI
from game.toontown.fishing.FishManagerAI import FishManagerAI
from game.toontown.fishing.FishBingoManagerAI import FishBingoManagerAI
from game.toontown.coghq.FactoryManagerAI import FactoryManagerAI
from game.toontown.coghq.MintManagerAI import MintManagerAI
from game.toontown.coghq.LawOfficeManagerAI import LawOfficeManagerAI
from game.toontown.coghq.CountryClubManagerAI import CountryClubManagerAI
from game.toontown.coghq.PromotionManagerAI import PromotionManagerAI
from game.toontown.coghq.CogSuitManagerAI import CogSuitManagerAI

from game.toontown.racing.DistributedRacePadAI import DistributedRacePadAI
from game.toontown.racing import RaceGlobals
from game.toontown.racing.DistributedViewPadAI import DistributedViewPadAI
from game.toontown.racing.DistributedStartingBlockAI import DistributedStartingBlockAI, DistributedViewingBlockAI
from game.toontown.racing.DistributedLeaderBoardAI import DistributedLeaderBoardAI
from game.toontown.racing.RaceManagerAI import RaceManagerAI
from game.toontown.ai.ToontownMagicWordManagerAI import ToontownMagicWordManagerAI
from game.toontown.parties.ToontownTimeManager import ToontownTimeManager
from game.toontown.ai.QuestManagerAI import QuestManagerAI
from game.toontown.tutorial.TutorialManagerAI import TutorialManagerAI
from game.toontown.safezone.DistributedPartyGateAI import DistributedPartyGateAI
from game.toontown.effects.DistributedFireworkShowAI import DistributedFireworkShowAI
from game.toontown.effects import FireworkShows
from game.otp.ai.BanManagerAI import BanManagerAI
from game.toontown.ai.CogPageManagerAI import CogPageManagerAI
from game.otp.friends.FriendManagerAI import FriendManagerAI
from game.toontown.coderedemption.TTCodeRedemptionMgrAI import TTCodeRedemptionMgrAI
from game.toontown.uberdog.DistributedPartyManagerAI import DistributedPartyManagerAI
from game.toontown.ai.DistributedPolarPlaceEffectMgrAI import DistributedPolarPlaceEffectMgrAI
from game.toontown.ai.DistributedResistanceEmoteMgrAI import DistributedResistanceEmoteMgrAI
from game.toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from game.toontown.estate.DistributedBankMgrAI import DistributedBankMgrAI
from game.toontown.ai.DialogueManagerAI import DialogueManagerAI
from game.otp.uberdog.OtpAvatarManagerAI import OtpAvatarManagerAI

import __builtin__, time, os, requests, random

__builtin__.isClient = lambda: PythonUtil.isClient()

class ToontownAIRepository(ToontownInternalRepository):
    notify = directNotify.newCategory('ToontownAIRepository')

    def __init__(self, baseChannel, districtName):
        ToontownInternalRepository.__init__(self, baseChannel, config.GetInt('air-stateserver', 0), dcSuffix = 'AI')

        self.districtName = districtName
        self.districtPopulation = 0

        self.zoneAllocator = UniqueIdAllocator(ToontownGlobals.DynamicZonesBegin, ToontownGlobals.DynamicZonesEnd)
        self.zoneDataStore = AIZoneDataStore()

        # Dictionaries:
        self.hoods = []
        self.zoneTable = {}
        self.cogHeadquarters = []
        self.dnaStoreMap = {}
        self.dnaDataMap = {}
        self.suitPlanners = {}
        self.buildingManagers = {}
        self.partyGates = []

        # What we want to have on the server:
        self.wantCogdominiums = config.GetBool('want-cogdominiums', False)
        self.useAllMinigames = config.GetBool('use-all-minigames', False)
        self.wantCodeRedemption = config.GetBool('want-coderedemption', False)

        self.cogSuitMessageSent = False

        # Enable logging.
        self.notify.setInfo(True)

    def getTrackClsends(self):
        if config.GetBool('want-track-clsends', False):
            return True

        return False

    def doLiveUpdates(self):
        if config.GetBool('want-do-live-updates', False):
            return True

        return False

    def sendToAPI(self, districtPopulation, decrease = False):
        if config.GetBool('want-localhost-api-testing', False):
            baseEndpoint = 'http://127.0.0.1:19135/api/{0}'
        else:
            baseEndpoint = 'http://otp-gs.rocketprogrammer.me:19135/api/{0}'

        if not decrease:
            endpoint = baseEndpoint.format('setPopulation')

            data = {
                'districtPopulation': districtPopulation
            }

            try:
                req = requests.post(endpoint, json = data)
            except:
                self.notify.warning('Failed to send district population to API!')
        else:
            endpoint = baseEndpoint.format('decreasePopulation')

            data = {
                'decreaseValue': districtPopulation
            }

            try:
                req = requests.post(endpoint, json = data)
            except:
                self.notify.warning('Failed to send district population decrease to API!')

    def incrementPopulation(self):
        self.districtPopulation += 1
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() + 1)
        self.sendToAPI(self.districtPopulation, False)

    def decrementPopulation(self):
        self.districtPopulation -= 1
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() - 1)
        self.sendToAPI(self.districtPopulation, True)

    def sendQueryToonMaxHp(self, doId, checkResult):
        if self.notify.getDebug():
            self.notify.debug('sendQueryToonMaxHp ({0}, {1})'.format(doId, checkResult))

    def _isValidPlayerLocation(self, parentId, zoneId):
        if not parentId or zoneId > ToontownGlobals.DynamicZonesEnd or zoneId is 0:
            return False

        return True

    def getAvatarExitEvent(self, doId):
        return 'distObjDelete-{0}'.format(doId)

    def getZoneDataStore(self):
        return self.zoneDataStore

    def sendSetZone(self, obj, zoneId):
        obj.b_setLocation(obj.parentId, zoneId)

    def allocateZone(self):
        return self.zoneAllocator.allocate()

    def deallocateZone(self, zone):
        self.zoneAllocator.free(zone)

    def getAvatarDisconnectReason(self, avId):
        return self.timeManager.avId2disconnectcode.get(avId, ToontownGlobals.DisconnectUnknown)

    def trueUniqueName(self, idString):
        return self.uniqueName(idString)

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        self.netMessenger.register(0, 'registerShard')
        self.netMessenger.register(2, 'postAddFriend')

        self.createObjects()

    def createObjects(self):
        self.districtId = self.allocateChannel()

        # Generate our district.
        self.district = ToontownDistrictAI(self)
        self.district.setName(self.districtName)
        self.district.generateWithRequiredAndId(self.districtId, self.getGameDoId(), OtpDoGlobals.OTP_ZONE_ID_DISTRICTS)
        self.district.setAI(self.ourChannel)

        self.districtStats = ToontownDistrictStatsAI(self)
        self.districtStats.settoontownDistrictId(self.districtId)
        self.districtStats.generateWithRequiredAndId(self.allocateChannel(), self.getGameDoId(), OtpDoGlobals.OTP_ZONE_ID_DISTRICTS_STATS)

        self.notify.info('Creating local objects...')
        self.createLocals()

        self.notify.info('Creating managers...')
        self.createManagers()

        self.notify.info('Creating zones...')
        self.createZones()

        self.district.b_setAvailable(1)

        # Inform the ExtAgent of us.
        self.netMessenger.send('registerShard', [self.districtId, config.GetString('air-shardname', 'District')])

    def createLocals(self):
        self.holidayManager = HolidayManagerAI(self)
        self.catalogManager = CatalogManagerAI(self)

        self.petMgr = PetManagerAI(self)
        self.suitInvasionManager = SuitInvasionManagerAI(self)

        self.fishManager = FishManagerAI(self)
        self.fishBingoManager = FishBingoManagerAI(self)

        self.factoryMgr = FactoryManagerAI(self)

        self.mintMgr = MintManagerAI(self)

        self.lawMgr = LawOfficeManagerAI(self)

        self.countryClubMgr = CountryClubManagerAI(self)

        self.raceMgr = RaceManagerAI(self)

        self.toontownTimeManager = ToontownTimeManager(serverTimeUponLogin = int(time.time()), globalClockRealTimeUponLogin = globalClock.getRealTime())

        self.banManager = BanManagerAI() # Disney's BanManager

        self.questManager = QuestManagerAI(self)

        self.promotionMgr = PromotionManagerAI(self)

        self.cogPageManager = CogPageManagerAI(self)

        self.cogSuitMgr = CogSuitManagerAI(self)

        self.dialogueManager = DialogueManagerAI(self)

    def createManagers(self):
        # Generate our TimeManagerAI.
        self.timeManager = TimeManagerAI(self)
        self.timeManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.welcomeValleyManager = WelcomeValleyManagerAI(self)
        self.welcomeValleyManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.inGameNewsMgr = DistributedInGameNewsMgrAI(self)
        self.inGameNewsMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.trophyMgr = DistributedTrophyMgrAI(self)
        self.trophyMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.newsManager = NewsManagerAI(self)
        self.newsManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.estateMgr = EstateManagerAI(self)
        self.estateMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.safeZoneManager = SafeZoneManagerAI(self)
        self.safeZoneManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.magicWordMgr = ToontownMagicWordManagerAI(self)
        self.magicWordMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.tutorialManager = TutorialManagerAI(self)
        self.tutorialManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.friendManager = FriendManagerAI(self)
        self.friendManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.deliveryManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER, 'DistributedDeliveryManager')

        self.codeRedemptionMgr = TTCodeRedemptionMgrAI(self)
        self.codeRedemptionMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.centralLogger = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_CENTRAL_LOGGER, 'CentralLogger')

        self.partyManager = DistributedPartyManagerAI(self)
        self.partyManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.dataStoreManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_TEMP_STORE_MANAGER, 'DistributedDataStoreManager')

        self.polarPlaceEffectMgr = DistributedPolarPlaceEffectMgrAI(self)
        self.polarPlaceEffectMgr.generateWithRequired(3821)

        self.resistanceEmoteMgr = DistributedResistanceEmoteMgrAI(self)
        self.resistanceEmoteMgr.generateWithRequired(9720)

        self.bankManager = DistributedBankMgrAI(self)
        self.bankManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.avatarManager = OtpAvatarManagerAI(self)
        self.avatarManager.generateWithRequiredAndId(2, self.getGameDoId(), 2)

    def createHood(self, hoodCtr, zoneId):
        # Bossbot HQ doesn't use DNA, so we skip over that.
        if zoneId != ToontownGlobals.BossbotHQ:
            self.dnaStoreMap[zoneId] = DNAStorage()
            self.dnaDataMap[zoneId] = self.loadDNAFileAI(self.dnaStoreMap[zoneId], self.genDNAFileName(zoneId))

            if zoneId in ToontownGlobals.HoodHierarchy:
                for streetId in ToontownGlobals.HoodHierarchy[zoneId]:
                    self.dnaStoreMap[streetId] = DNAStorage()
                    self.dnaDataMap[streetId] = self.loadDNAFileAI(self.dnaStoreMap[streetId], self.genDNAFileName(streetId))

        hood = hoodCtr(self, zoneId)
        hood.startup()
        self.hoods.append(hood)

    def createZones(self):
        # First, generate our zone2NpcDict...
        NPCToons.generateZone2NpcDict()

        # If enabled, create our main playgrounds:
        if config.GetBool('want-main-playgrounds', True):
            self.createMainPlaygrounds()

        # If enabled, create our Cog HQs:
        if config.GetBool('want-cog-headquarters', True):
            self.createCogHeadquarters()

        # If enabled, create our other playgrounds:
        if config.GetBool('want-other-playgrounds', True):
            self.createMiscPlaygrounds()

    def createMainPlaygrounds(self):
        # Toontown Central
        self.zoneTable[ToontownGlobals.ToontownCentral] = (
            (ToontownGlobals.ToontownCentral, 1, 0), (ToontownGlobals.SillyStreet, 1, 1),
            (ToontownGlobals.LoopyLane, 1, 1),
            (ToontownGlobals.PunchlinePlace, 1, 1)
        )
        self.createHood(TTHoodDataAI, ToontownGlobals.ToontownCentral)

        # Donald's Dock
        self.zoneTable[ToontownGlobals.DonaldsDock] = (
            (ToontownGlobals.DonaldsDock, 1, 0), (ToontownGlobals.BarnacleBoulevard, 1, 1),
            (ToontownGlobals.SeaweedStreet, 1, 1), (ToontownGlobals.LighthouseLane, 1, 1)
        )
        self.createHood(DDHoodDataAI, ToontownGlobals.DonaldsDock)

        # Daisy Gardens
        self.zoneTable[ToontownGlobals.DaisyGardens] = (
            (ToontownGlobals.DaisyGardens, 1, 0), (ToontownGlobals.ElmStreet, 1, 1),
            (ToontownGlobals.MapleStreet, 1, 1), (ToontownGlobals.OakStreet, 1, 1)
        )
        self.createHood(DGHoodDataAI, ToontownGlobals.DaisyGardens)

        # Minnie's Melodyland
        self.zoneTable[ToontownGlobals.MinniesMelodyland] = (
            (ToontownGlobals.MinniesMelodyland, 1, 0), (ToontownGlobals.AltoAvenue, 1, 1),
            (ToontownGlobals.BaritoneBoulevard, 1, 1), (ToontownGlobals.TenorTerrace, 1, 1)
        )
        self.createHood(MMHoodDataAI, ToontownGlobals.MinniesMelodyland)

        # The Brrrgh
        self.zoneTable[ToontownGlobals.TheBrrrgh] = (
            (ToontownGlobals.TheBrrrgh, 1, 0), (ToontownGlobals.WalrusWay, 1, 1),
            (ToontownGlobals.SleetStreet, 1, 1), (ToontownGlobals.PolarPlace, 1, 1)
        )
        self.createHood(BRHoodDataAI, ToontownGlobals.TheBrrrgh)

        # Donald's Dreamland
        self.zoneTable[ToontownGlobals.DonaldsDreamland] = (
            (ToontownGlobals.DonaldsDreamland, 1, 0), (ToontownGlobals.LullabyLane, 1, 1),
            (ToontownGlobals.PajamaPlace, 1, 1)
        )
        self.createHood(DLHoodDataAI, ToontownGlobals.DonaldsDreamland)

    def createCogHeadquarters(self):
        # Sellbot HQ
        self.zoneTable[ToontownGlobals.SellbotHQ] = (
            (ToontownGlobals.SellbotHQ, 0, 1), (ToontownGlobals.SellbotFactoryExt, 0, 1)
        )
        self.createHood(CSHoodDataAI, ToontownGlobals.SellbotHQ)

        # Cashbot HQ
        self.zoneTable[ToontownGlobals.CashbotHQ] = (
            (ToontownGlobals.CashbotHQ, 0, 1),
        )
        self.createHood(CashbotHQDataAI, ToontownGlobals.CashbotHQ)

        # Lawbot HQ
        self.zoneTable[ToontownGlobals.LawbotHQ] = (
            (ToontownGlobals.LawbotHQ, 0, 1),
        )
        self.createHood(LawbotHQDataAI, ToontownGlobals.LawbotHQ)

        # Bossbot HQ
        self.zoneTable[ToontownGlobals.BossbotHQ] = (
            (ToontownGlobals.BossbotHQ, 0, 0),
        )
        self.createHood(BossbotHQDataAI, ToontownGlobals.BossbotHQ)

    def createMiscPlaygrounds(self):
        # Goofy Speedway
        self.zoneTable[ToontownGlobals.GoofySpeedway] = (
            (ToontownGlobals.GoofySpeedway, 1, 0),
        )
        self.createHood(GSHoodDataAI, ToontownGlobals.GoofySpeedway)

        # Chip 'n Dale's Acorn Acres
        self.zoneTable[ToontownGlobals.OutdoorZone] = (
            (ToontownGlobals.OutdoorZone, 1, 0),
        )
        self.createHood(OZHoodDataAI, ToontownGlobals.OutdoorZone)

        # Chip 'n Dale's MiniGolf
        self.zoneTable[ToontownGlobals.GolfZone] = (
            (ToontownGlobals.GolfZone, 1, 0),
        )
        self.createHood(GZHoodDataAI, ToontownGlobals.GolfZone)

        # Welcome Valley hoods (Toontown Central & Goofy Speedway)
        self.welcomeValleyManager.createWelcomeValleyHoods()

        # Assign the initial suit buildings.
        self.notify.info('Assigning initial Cog buildings and Field Offices...')

        for suitPlanner in self.suitPlanners.values():
            suitPlanner.assignInitialSuitBuildings()

        # Let our user know we have finished starting up.
        self.notify.info('{0} has finished starting up.'.format(self.districtName))

        # Fireworks task.
        thetime = time.time() % 3600

        if thetime < 60:
            taskMgr.doMethodLater(1, self.startFireworks, 'fireworks-taskmgr-hourly')
        else:
            taskMgr.doMethodLater(3600 - thetime, self.startFireworks, 'fireworks-taskmgr-hourly')

    def loadDNAFileAI(self, dnaStore, dnaFileName):
        resourcesPath = 'game/resources/'

        if not dnaFileName.startswith(resourcesPath):
            dnaFileName = resourcesPath + dnaFileName

        return loadDNAFileAI(dnaStore, dnaFileName)

    def genDNAFileName(self, zoneId):
        zoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        hoodId = ZoneUtil.getCanonicalHoodId(zoneId)
        hood = ToontownGlobals.dnaMap[hoodId]

        if hoodId == zoneId:
            zoneId = 'sz'
            phase = ToontownGlobals.phaseMap[hoodId]
        else:
            phase = ToontownGlobals.streetPhaseMap[hoodId]

        if 'outdoor_zone' in hood or 'golf_zone' in hood:
            phase = '6'

        return 'phase_{0}/dna/{1}_{2}.dna'.format(phase, hood, zoneId)

    def lookupDNAFileName(self, dnaFileName):
        for _ in xrange(3, 13):
            if os.path.exists('game/resources/phase_{0}/dna/{1}'.format(_, dnaFileName)):
                return 'phase_{0}/dna/{1}'.format(_, dnaFileName)

    def findFishingPonds(self, dnaData, zoneId, area):
        fishingPonds = []
        fishingPondGroups = []

        if isinstance(dnaData, DNAGroup) and 'fishing_pond' in dnaData.getName():
            fishingPondGroups.append(dnaData)
            pond = self.fishManager.generatePond(area, zoneId)
            fishingPonds.append(pond)
        else:
            if isinstance(dnaData, DNAVisGroup):
                zoneId = ZoneUtil.getTrueZoneId(int(dnaData.getName().split(':')[0]), zoneId)

        for i in xrange(dnaData.getNumChildren()):
            foundFishingPonds, foundFishingPondGroups = self.findFishingPonds(dnaData.at(i), zoneId, area)
            fishingPonds.extend(foundFishingPonds)
            fishingPondGroups.extend(foundFishingPondGroups)

        return (fishingPonds, fishingPondGroups)

    def findFishingSpots(self, dnaData, fishingPond):
        fishingSpots = []

        if isinstance(dnaData, DNAGroup) and dnaData.getName()[:13] == 'fishing_spot_':
            spot = self.fishManager.generateSpots(dnaData, fishingPond)
            fishingSpots.append(spot)

        for i in xrange(dnaData.getNumChildren()):
            foundFishingSpots = self.findFishingSpots(dnaData.at(i), fishingPond)
            fishingSpots.extend(foundFishingSpots)

        return fishingSpots

    def findRacingPads(self, dnaData, zoneId, area, type = 'racing_pad', overrideDNAZone = False):
        racingPads, racingPadGroups = [], []

        if type in dnaData.getName():
            if type == 'racing_pad':
                nameSplit = dnaData.getName().split('_')
                racePad = DistributedRacePadAI(self)
                racePad.setArea(area)
                racePad.index = int(nameSplit[2])
                racePad.genre = nameSplit[3]
                trackInfo = RaceGlobals.getNextRaceInfo(-1, racePad.genre, racePad.index)
                racePad.setTrackInfo([trackInfo[0], trackInfo[1]])
                racePad.laps = trackInfo[2]
                racePad.generateWithRequired(zoneId)
                racingPads.append(racePad)
                racingPadGroups.append(dnaData)

            elif type == 'viewing_pad':
                viewPad = DistributedViewPadAI(self)
                viewPad.setArea(area)
                viewPad.generateWithRequired(zoneId)
                racingPads.append(viewPad)
                racingPadGroups.append(dnaData)

        for i in xrange(dnaData.getNumChildren()):
            foundRacingPads, foundRacingPadGroups = self.findRacingPads(dnaData.at(i), zoneId, area, type, overrideDNAZone)
            racingPads.extend(foundRacingPads)
            racingPadGroups.extend(foundRacingPadGroups)

        return (racingPads, racingPadGroups)

    def findStartingBlocks(self, dnaData, pad):
        startingBlocks = []

        for i in xrange(dnaData.getNumChildren()):
            groupName = dnaData.getName()
            blockName = dnaData.at(i).getName()

            if 'starting_block' in blockName:
                cls = DistributedStartingBlockAI if 'racing_pad' in groupName else DistributedViewingBlockAI
                x, y, z = dnaData.at(i).getPos()
                h, p, r = dnaData.at(i).getHpr()
                padLocationId = int(dnaData.at(i).getName()[(-1)])
                startingBlock = cls(self, pad, x, y, z, h, p, r, padLocationId)
                startingBlock.generateWithRequired(pad.zoneId)
                startingBlocks.append(startingBlock)

        return startingBlocks

    def findLeaderBoards(self, dnaData, zoneId):
        leaderboards = []
        if 'leaderBoard' in dnaData.getName():
            x, y, z = dnaData.getPos()
            h, p, r = dnaData.getHpr()
            leaderboard = DistributedLeaderBoardAI(self, dnaData.getName(), x, y, z, h, p, r)
            leaderboard.generateWithRequired(zoneId)
            leaderboards.append(leaderboard)
        for i in xrange(dnaData.getNumChildren()):
            foundLeaderBoards = self.findLeaderBoards(dnaData.at(i), zoneId)
            leaderboards.extend(foundLeaderBoards)

        return leaderboards

    def findPartyHats(self, dnaData, zoneId):
        partyHats = []

        if 'prop_party_gate' in dnaData.getName():
            partyHat = DistributedPartyGateAI(self)
            partyHat.generateWithRequired(zoneId)
            partyHats.append(partyHat)
            self.partyGates.append(partyHat)

        for i in xrange(dnaData.getNumChildren()):
            foundPartyHats = self.findPartyHats(dnaData.at(i), zoneId)
            partyHats.extend(foundPartyHats)

        return partyHats

    def startFireworks(self, task):
        if simbase.air.holidayManager.isHolidayRunning(ToontownGlobals.COMBO_FIREWORKS):
            allFwTypes = [ToontownGlobals.NEWYEARS_FIREWORKS, ToontownGlobals.JULY4_FIREWORKS]
            fwType = allFwTypes[random.randint(0, len(allFwTypes) - 1)]
            numShows = len(FireworkShows.shows.get(fwType, []))
            showIndex = random.randint(0, numShows - 1)
            for hood in simbase.air.hoods:
                if hood.zoneId == ToontownGlobals.GolfZone:
                    continue
                fwShow = DistributedFireworkShowAI(simbase.air)
                fwShow.generateWithRequired(hood.zoneId)
                fwShow.d_startShow(fwType, showIndex)
        task.delayTime = 3600
        return task.again

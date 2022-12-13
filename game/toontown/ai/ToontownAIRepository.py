from panda3d.core import UniqueIdAllocator, CSDefault, DSearchPath, Filename
from panda3d.toontown import DNAStorage, loadDNAFileAI, DNAGroup, DNAVisGroup, loadDNAFile, DNAProp

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task import Task

from game.otp.ai import TimeManagerAI
from game.toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
from game.toontown.distributed.ToontownDistrictStatsAI import ToontownDistrictStatsAI
from game.toontown.ai.HolidayManagerAI import HolidayManagerAI
from game.toontown.toonbase import ToontownGlobals
from game.toontown.catalog.CatalogManagerAI import CatalogManagerAI
from game.otp.distributed import OtpDoGlobals
from game.otp.ai.AIZoneData import AIZoneDataStore
from game.toontown.ai import WelcomeValleyManagerAI
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
from game.toontown.building import DistributedTrophyMgrAI
from game.toontown.pets.PetManagerAI import PetManagerAI
from game.toontown.suit.SuitInvasionManagerAI import SuitInvasionManagerAI
from game.toontown.ai.NewsManagerAI import NewsManagerAI
from game.toontown.estate.EstateManagerAI import EstateManagerAI
from game.toontown.safezone.SafeZoneManagerAI import SafeZoneManagerAI
from game.toontown.fishing.FishManagerAI import FishManagerAI
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
from game.toontown.parties import ToontownTimeManager
from game.toontown.quest import QuestManagerAI
from game.toontown.tutorial.TutorialManagerAI import TutorialManagerAI
from game.toontown.safezone.DistributedPartyGateAI import DistributedPartyGateAI
from game.otp.ai.BanManagerAI import BanManagerAI
from game.toontown.shtiker import CogPageManagerAI
from game.otp.friends.FriendManagerAI import FriendManagerAI
from game.toontown.coderedemption.TTCodeRedemptionMgrAI import TTCodeRedemptionMgrAI
from game.toontown.uberdog.DistributedPartyManagerAI import DistributedPartyManagerAI
from game.toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from game.toontown.estate import DistributedBankMgrAI
from game.otp.uberdog.OtpAvatarManagerAI import OtpAvatarManagerAI
from game.toontown.uberdog.ServerBase import ServerBase
from game.otp.otpbase import OTPGlobals
from game.toontown.ai import ToontownAIMsgTypes
from game.toontown.toon.NPCDialogueManagerAI import NPCDialogueManagerAI
from game.toontown.uberdog.ExtAgent import ServerGlobals
from game.toontown.safezone import DistributedFishingSpotAI
from game.toontown.fishing import DistributedFishingPondAI

import time, requests, functools

class ToontownAIRepository(ToontownInternalRepository, ServerBase):
    notify = directNotify.newCategory('ToontownAIRepository')

    def __init__(self, baseChannel, districtName):
        ToontownInternalRepository.__init__(self, baseChannel, config.GetInt('air-stateserver', 0), dcSuffix = 'AI')
        ServerBase.__init__(self)

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

        # Guard for publish
        if simbase.wantBingo:
            self.bingoMgr = None

        # Record the reason each client leaves the shard, according to
        # the client.
        self._avatarDisconnectReasons = {}

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

    def sendPopulation(self):
        data = {
            'token': config.GetString('api-token'),
            'population': self.districtPopulation,
            'serverType': ServerGlobals.FINAL_TOONTOWN,
            'shardName': self.districtName,
            'shardId': self.districtId
        }

        headers = {
            'User-Agent': 'Sunrise Games - ToontownAIRepository'
        }

        try:
            requests.post('https://api.sunrise.games/api/setPopulation', json = data, headers = headers)
        except:
            self.notify.warning('Failed to send district population!')

    def incrementPopulation(self):
        self.districtPopulation += 1
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() + 1)

        if self.isProdServer():
            # This is the production server.
            # Send our population increase.
            self.sendPopulation()

    def decrementPopulation(self):
        self.districtPopulation -= 1
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() - 1)

        if self.isProdServer():
            # This is the production server.
            # Send our population decrease.
            self.sendPopulation()

    def sendQueryToonMaxHp(self, doId, checkResult):
        if self.notify.getDebug():
            self.notify.debug(f'sendQueryToonMaxHp ({doId}, {checkResult})')

    def _isValidPlayerLocation(self, parentId, zoneId):
        if not parentId or zoneId > ToontownGlobals.DynamicZonesEnd or zoneId == 0:
            return False

        return True

    def getAvatarExitEvent(self, doId):
        return f'distObjDelete-{doId}'

    def getZoneDataStore(self):
        return self.zoneDataStore

    def sendSetZone(self, obj, zoneId):
        obj.b_setLocation(obj.parentId, zoneId)

    def allocateZone(self):
        return self.zoneAllocator.allocate()

    def deallocateZone(self, zone):
        self.zoneAllocator.free(zone)

    def trueUniqueName(self, idString):
        return self.uniqueName(idString)

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        self.netMessenger.register(0, 'registerShard')
        self.netMessenger.register(2, 'postAddFriend')
        self.netMessenger.register(6, 'refreshModules')

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

        # mark district as avaliable
        self.district.b_setAvailable(1)

        # Now that everything's created, start checking the leader
        # boards for correctness.  We only need to check every 30
        # seconds or so.
        self.__leaderboardFlush(None)
        taskMgr.doMethodLater(30, self.__leaderboardFlush,
                              'leaderboardFlush', appendTask = True)

        # Inform the ExtAgent of us.
        self.netMessenger.send('registerShard', [self.districtId, self.districtName])

        # Start our invasion API task.
        taskMgr.doMethodLater(15, self.updateInvasionAPI, f"updateInvasionAPI-{self.districtName}")

    def updateInvasionAPI(self, task):
        if self.suitInvasionManager.getInvading() and self.air.isProdServer():
            # Update our invasion status for the API.
            self.air.suitInvasionManager.sendToAPI("updateInvasion")
        return Task.again

    def __leaderboardFlush(self, task):
        messenger.send('leaderboardFlush')
        return Task.again

    def createLocals(self):
        self.holidayManager = HolidayManagerAI(self)
        self.catalogManager = CatalogManagerAI(self)

        self.petMgr = PetManagerAI(self)
        self.suitInvasionManager = SuitInvasionManagerAI(self)

        self.fishManager = FishManagerAI(self)

        self.factoryMgr = FactoryManagerAI(self)

        self.mintMgr = MintManagerAI(self)

        self.lawMgr = LawOfficeManagerAI(self)

        self.countryClubMgr = CountryClubManagerAI(self)

        self.raceMgr = RaceManagerAI(self)

        self.toontownTimeManager = ToontownTimeManager.ToontownTimeManager()
        self.toontownTimeManager.updateLoginTimes(time.time(), time.time(), globalClock.getRealTime())

        self.banManager = BanManagerAI() # Disney's BanManager

        # The Quest manager
        self.questManager = QuestManagerAI.QuestManagerAI(self)

        self.promotionMgr = PromotionManagerAI(self)

        # The Cog Page manager
        self.cogPageManager = CogPageManagerAI.CogPageManagerAI(self)

        self.cogSuitMgr = CogSuitManagerAI(self)

        self.dialogueManager = NPCDialogueManagerAI()

    def createManagers(self):
        # The Time manager.  This negotiates a timestamp exchange for
        # the purposes of synchronizing clocks between client and
        # server with a more accurate handshaking protocol than we
        # would otherwise get.
        #
        # We must create this object first, so clients who happen to
        # come into the world while the AI is still coming up
        # (particularly likely if the AI crashed while players were
        # in) will get a chance to synchronize.
        self.timeManager = TimeManagerAI.TimeManagerAI(self)
        # self.timeManager.generateOtpObject(
            # self.district.getDoId(), OTPGlobals.UberZone)
        # TODO: Why can't we use generateOtpObject here?
        self.timeManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.welcomeValleyManager = WelcomeValleyManagerAI.WelcomeValleyManagerAI(self)
        self.welcomeValleyManager.generateWithRequired(OTPGlobals.UberZone)

        self.inGameNewsMgr = DistributedInGameNewsMgrAI(self)
        self.inGameNewsMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        # The trophy manager should be created before the building
        # managers.
        self.trophyMgr = DistributedTrophyMgrAI.DistributedTrophyMgrAI(self)
        self.trophyMgr.generateWithRequired(OTPGlobals.UberZone)

        self.newsManager = NewsManagerAI(self)
        self.newsManager.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        self.estateMgr = EstateManagerAI(self)
        self.estateMgr.generateWithRequired(OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

        # HACK: Start listening to estate events in the pet manager...
        self.petMgr.listenEvents()

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
        self.partyManager.generateOtpObject(self.district.getDoId(), OTPGlobals.UberZone)

        self.dataStoreManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_TEMP_STORE_MANAGER, 'DistributedDataStoreManager')

        # The bank manager handles banking transactions
        self.bankMgr = DistributedBankMgrAI.DistributedBankMgrAI(self)
        self.bankMgr.generateWithRequired(OTPGlobals.UberZone)

        self.avatarManager = OtpAvatarManagerAI(self)
        self.avatarManager.generateWithRequiredAndId(self.allocateChannel(), self.getGameDoId(), OtpDoGlobals.OTP_ZONE_ID_MANAGEMENT)

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

        # Assign the initial suit buildings.
        self.notify.info('Assigning initial Cog buildings and Field Offices...')

        for suitPlanner in list(self.suitPlanners.values()):
            suitPlanner.assignInitialSuitBuildings()

        # These are required so the scientists can talk.
        self.holidayManager.startHoliday(ToontownGlobals.SILLYMETER_HOLIDAY)
        self.holidayManager.startHoliday(ToontownGlobals.SILLYMETER_EXT_HOLIDAY)

        # Let our user know we have finished starting up.
        self.notify.info(f'{self.districtName} has finished starting up.')

    def loadDNAFileAI(self, dnaStore, dnaFile):
        return loadDNAFileAI(dnaStore, dnaFile, CSDefault)

    #AIGEOM
    def loadDNAFile(self, dnaStore, dnaFile, cs=CSDefault):
        """
        load everything, including geometry
        """
        return loadDNAFile(dnaStore, dnaFile, cs)

    def startupHood(self, hoodDataAI):
        hoodDataAI.startup()
        self.hoods.append(hoodDataAI)

    def shutdownHood(self, hoodDataAI):
        hoodDataAI.shutdown()
        self.hoods.remove(hoodDataAI)

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

        return f'phase_{phase}/dna/{hood}_{zoneId}.dna'

    def lookupDNAFileName(self, dnaFileName):
        searchPath = DSearchPath()
        searchPath.appendDirectory(Filename('game/resources/phase_3.5/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_4/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_5/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_5.5/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_6/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_8/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_9/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_10/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_11/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_12/dna'))
        searchPath.appendDirectory(Filename('game/resources/phase_13/dna'))
        filename = Filename(dnaFileName)
        found = vfs.resolveFilename(filename, searchPath)
        if not found:
            self.notify.warning(f'lookupDNAFileName - {dnaFileName} not found on:')
            print(searchPath)
        else:
            return filename.getFullpath()

    def findFishingPonds(self, dnaGroup, zoneId, area, overrideDNAZone = 0):
        """
                Recursively scans the given DNA tree for fishing ponds.  These
                are defined as all the groups whose code includes the string
                "fishing_pond".  For each such group, creates a
                DistributedFishingPondAI.  Returns the list of distributed
                objects and a list of the DNAGroups so we can search them for
                spots and targets.
                """
        fishingPonds = []
        fishingPondGroups = []

        if ((isinstance(dnaGroup, DNAGroup)) and
                # If it is a DNAGroup, and the name starts with fishing_pond, count it
                (dnaGroup.getName().find('fishing_pond') >= 0)):
            # Here's a fishing pond!
            fishingPondGroups.append(dnaGroup)
            fp = DistributedFishingPondAI.DistributedFishingPondAI(self, area)
            fp.generateWithRequired(zoneId)
            fishingPonds.append(fp)
        else:
            # Now look in the children
            # Fishing ponds cannot have other ponds in them,
            # so do not search the one we just found:
            # If we come across a visgroup, note the zoneId and then recurse
            if (isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone):
                # Make sure we get the real zone id, in case we are in welcome valley
                zoneId = ZoneUtil.getTrueZoneId(
                    int(dnaGroup.getName().split(':')[0]), zoneId)
            for i in range(dnaGroup.getNumChildren()):
                childFishingPonds, childFishingPondGroups = self.findFishingPonds(
                    dnaGroup.at(i), zoneId, area, overrideDNAZone)
                fishingPonds += childFishingPonds
                fishingPondGroups += childFishingPondGroups
        return fishingPonds, fishingPondGroups

    def findFishingSpots(self, dnaPondGroup, distPond):
        """
        Scans the given DNAGroup pond for fishing spots.  These
        are defined as all the props whose code includes the string
        "fishing_spot".  Fishing spots should be the only thing under a pond
        node. For each such prop, creates a DistributedFishingSpotAI.
        Returns the list of distributed objects created.
        """
        fishingSpots = []
        # Search the children of the pond
        for i in range(dnaPondGroup.getNumChildren()):
            dnaGroup = dnaPondGroup.at(i)
            if ((isinstance(dnaGroup, DNAProp)) and (dnaGroup.getCode().find('fishing_spot') >= 0)):
                # Here's a fishing spot!
                pos = dnaGroup.getPos()
                hpr = dnaGroup.getHpr()
                fs = DistributedFishingSpotAI.DistributedFishingSpotAI(
                     self, distPond, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                fs.generateWithRequired(distPond.zoneId)
                fishingSpots.append(fs)
            else:
                self.notify.debug("Found dnaGroup that is not a fishing_spot under a pond group")
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

        for i in range(dnaData.getNumChildren()):
            foundRacingPads, foundRacingPadGroups = self.findRacingPads(dnaData.at(i), zoneId, area, type, overrideDNAZone)
            racingPads.extend(foundRacingPads)
            racingPadGroups.extend(foundRacingPadGroups)

        return (racingPads, racingPadGroups)

    def findStartingBlocks(self, dnaData, pad):
        startingBlocks = []

        for i in range(dnaData.getNumChildren()):
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

    def findLeaderBoards(self, dnaPool, zoneID):
        '''
        Find and return leader boards
        '''
        leaderBoards = []
        if (dnaPool.getName().find('leaderBoard') >= 0):
            #found a leader board
            pos = dnaPool.getPos()
            hpr = dnaPool.getHpr()

            lb = DistributedLeaderBoardAI(self, dnaPool.getName(), zoneID, [], pos, hpr)
            lb.generateWithRequired(zoneID)
            leaderBoards.append(lb)
        else:
            for i in range(dnaPool.getNumChildren()):
                result = self.findLeaderBoards(dnaPool.at(i), zoneID)
                if result:
                    leaderBoards += result

        return leaderBoards

    def findPartyHats(self, dnaData, zoneId):
        partyHats = []

        if 'prop_party_gate' in dnaData.getName():
            partyHat = DistributedPartyGateAI(self)
            partyHat.generateWithRequired(zoneId)
            partyHats.append(partyHat)
            self.partyGates.append(partyHat)

        for i in range(dnaData.getNumChildren()):
            foundPartyHats = self.findPartyHats(dnaData.at(i), zoneId)
            partyHats.extend(foundPartyHats)

        return partyHats

    def handleDatagram(self, di):
        msgType = self.getMsgType()

        if msgType == ToontownAIMsgTypes.PARTY_MANAGER_UD_TO_ALL_AI:
            self.__handlePartyManagerUdToAllAi(di)
            return

        ToontownInternalRepository.handleDatagram(self, di)

    def __handlePartyManagerUdToAllAi(self,di):
        """Send all msgs of this type to the party manager on our district."""
        # we know the format is STATE_SERVER_OBJECT_UPDATE_FIELD
        # we just changed the msg type to PARTY_MANAGER_UD_TO_ALL_AI
        # so that it gets handled here
        # otherwise it just gets dropped on the floor
        do = self.partyManager
        if do:
            globalId = di.getUint32()
            if globalId != OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER:
                self.notify.error('__handlePartyManagerUdToAllAi globalId=%d not equal to %d' %
                                  (globalId, OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER))
            # Let the dclass finish the job
            do.dclass.receiveUpdate(do, di)

    def handleAvCatch(self, avId, zoneId, catch):
        """
        avId - ID of avatar to update
        zoneId - zoneId of the pond the catch was made in.
                This is used by the BingoManagerAI to
                determine which PBMgrAI needs to update
                the catch.
        catch - a fish tuple of (genus, species)
        returns: None

        This method instructs the BingoManagerAI to
        tell the appropriate PBMgrAI to update the
        catch of an avatar at the particular pond. This
        method is called in the FishManagerAI's
        RecordCatch method.
        """
        # Guard for publish
        if simbase.wantBingo:
            if self.bingoMgr:
                self.bingoMgr.setAvCatchForPondMgr(avId, zoneId, catch)

    def createPondBingoMgrAI(self, estate):
        """
        estate - the estate for which the PBMgrAI should
                be created.
        returns: None

        This method instructs the BingoManagerAI to
        create a new PBMgrAI for a newly generated
        estate.
        """
        # Guard for publish
        if simbase.wantBingo:
            if self.bingoMgr:
                self.notify.info('createPondBingoMgrAI: Creating a DPBMAI for Dynamic Estate')
                self.bingoMgr.createPondBingoMgrAI(estate, 1)

    def getEstate(self, avId, accId, zoneId, callback):
        self.notify.debug(f'getEstate avId={avId}, accId={accId}, zoneId={zoneId}, callback={callback}')
        estateId = 0
        estateVal = {} # {estateFieldName: packedValues}
        avIds = []

        avatars = {} # {avId: {fieldName: [fieldValue]}}

        def __handleGetEstate(dclass, fields):
            if dclass != self.dclassesByName['DistributedEstateAI']:
                self.notify.warning(
                    'Account %d has non-estate dclass %d!' % (accId, dclass)
                )
                return

            nonlocal estateVal
            # Convert Astron response to OTP
            estateVal = self.packDclassValueDict(dclass, fields)

            # Now to do the houses:
            self.getHouses(avId, accId, zoneId, estateId, estateVal, avIds, avatars, callback)


        def __gotAllAvatars():
            self.notify.debug(f'__gotAllAvatars: {estateId, avIds, len(avatars)}')

            if estateId:
                self.dbInterface.queryObject(self.dbId, estateId, __handleGetEstate)
            else:
                def __handleEstateCreated(newEstateId):
                    nonlocal estateId
                    estateId = newEstateId
                    # Update Account object with the new estate id
                    self.dbInterface.updateObject(self.dbId, accId, self.dclassesByName['AccountAI'],
                                                          {'ESTATE_ID': estateId})

                    self.dbInterface.queryObject(self.dbId, estateId, __handleGetEstate)

                self.dbInterface.createObject(self.dbId, self.dclassesByName['DistributedEstateAI'], {},
                                                  __handleEstateCreated)


        def __handleGetAvatar(dclass, fields, index):
            if dclass != self.dclassesByName['DistributedToonAI']:
                self.notify.warning(
                    'Account %d has avatar %d with non-Toon dclass %d!' % (accId, avIds[index], dclass))
                # FIXME: idk what to do here? ~LC
                return


            fields['avId'] = avIds[index]
            avatars[index] = fields
            if len(avatars) == 6:
                __gotAllAvatars()

        def __handleGetAccount(dclass, fields):
            if dclass != self.dclassesByName['AccountAI']:
                self.notify.warning('Account %d has non-account dclass %d!' % (accId, dclass))
                # FIXME: idk what to do here? ~LC
                return

            nonlocal estateId, avIds, avatars
            estateId = fields.get('ESTATE_ID', 0)
            avIds = fields.get('ACCOUNT_AV_SET', [0] * 6)
            # HACK: Sanitize the avIds list in case its too long/short
            avIds = avIds[:6]
            avIds += [0] * (6 - len(avIds))
            for index, avId in enumerate(avIds):
                if avId == 0:
                    avatars[index] = None
                    continue

                # Get the avatar object for each avId.
                self.dbInterface.queryObject(self.dbId, avId,
                                             functools.partial(__handleGetAvatar, index=index))

        # Get the account object.
        self.dbInterface.queryObject(self.dbId, accId, __handleGetAccount)

    def getHouses(self, avId, accId, zoneId, estateId, estateVal, avIds, avatars, callback):
        '''
        Continuation of getEstate
        '''
        self.notify.debug(f'getHouses avId={avId}, accId={accId}, zoneId={zoneId}, estateId={estateId}, avIds={avIds}, callback={callback}')

        # numHouses = 0
        houseIds = [0] * len(avIds)
        houseVal = [None] * len(avIds) # [packedHouseValues]

        def __gotAllHouses():
            # Get pet ids
            petIds = [0] * len(avIds)
            for index in avatars:
                if avatars[index] != None:
                    petId = avatars[index].get('setPetId', [0])[0]
                    if petId != 0:
                        petIds[index] = petId

            # Get Gardens started.
            gardensStarted = [False] * len(avIds)
            for index in avatars:
                if avatars[index] != None:
                    gardenStarted = avatars[index].get('setGardenStarted', [0])[0]
                    if gardenStarted:
                        gardensStarted[index] = True

            self.notify.debug(f'__gotAllHouses {estateId, estateVal, len(houseIds), houseIds, houseVal, petIds, gardensStarted, estateVal}')

            # That's a lot of work, time to finally call our callback.  Whew!
            callback(estateId, estateVal, len(houseIds), houseIds, houseVal,
                     petIds, gardensStarted, estateVal)

        def __handleGetHouse(dclass, fields, index):
            nonlocal houseVal
            if dclass != self.dclassesByName['DistributedHouseAI']:
                self.notify.warning('Avatar %d has non-house object %d with dclass %d!' % (avIds[index], houseId, dclass))
                return

            # Set the most important fields here.
            fields['setAvatarId'] = [avIds[index]]
            fields['setName'] = avatars[index]['setName']

            # Convert Astron response to OTP
            houseVal[index] = self.packDclassValueDict(dclass, fields)

            if None not in houseVal:
                __gotAllHouses()

        def __handleHouseCreated(houseId, index):
            nonlocal houseIds, houseVal

            houseIds[index] = houseId
            av = self.doId2do.get(avIds[index])
            if av:
                # Update house id
                av.b_setHouseId(houseId)
            else:
                self.dbInterface.updateObject(self.dbId, avIds[index],
                                                      self.dclassesByName['DistributedToonAI'],
                                                      {'setHouseId': [houseId]})

            # self.dbInterface.queryObject(self.dbId, houseId,
                                         # functools.partial(__handleGetHouse, index=index))
            __handleGetHouse(self.dclassesByName['DistributedHouseAI'], {}, index)


        for index in avatars:
            if avatars[index] == None:
                # No avatar, no house. Allocate an ID in it's place
                # (it'll be generated into an empty house)
                houseId = self.allocateChannel()
                houseIds[index] = houseId
                houseVal[index] = {}
                if None not in houseVal:
                    __gotAllHouses()
                    return
                else:
                    continue
            houseId = avatars[index].get('setHouseId', [0])[0]
            if houseId == 0:
                # No house
                self.dbInterface.createObject(self.dbId, self.dclassesByName['DistributedHouseAI'],
                                              {},
                                              #{'setName': [avatars[index]['setName'][0]],
                                              # 'setAvatarId': [avatars[index]['avId']]},
                                              functools.partial(__handleHouseCreated, index=index))
            else:
                houseIds[index] = houseId
                self.dbInterface.queryObject(self.dbId, houseId,
                                             functools.partial(__handleGetHouse, index=index))


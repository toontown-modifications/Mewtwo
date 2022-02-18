from panda3d.core import BitMask32

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from game.otp.otpbase import OTPGlobals

from game.toontown.estate import CannonGlobals
from game.toontown.estate import GardenGlobals
from game.toontown.estate import HouseGlobals
from game.toontown.estate.DistributedCannonAI import DistributedCannonAI
from game.toontown.estate.DistributedTargetAI import DistributedTargetAI
from game.toontown.estate.DistributedFireworksCannonAI import DistributedFireworksCannonAI
from game.toontown.estate.DistributedGardenAI import DistributedGardenAI
from game.toontown.fishing.DistributedFishingPondAI import DistributedFishingPondAI
from game.toontown.safezone.DistributedFishingSpotAI import DistributedFishingSpotAI
from game.toontown.safezone.EFlyingTreasurePlannerAI import EFlyingTreasurePlannerAI
from game.toontown.safezone.ETreasurePlannerAI import ETreasurePlannerAI
from game.toontown.toonbase import ToontownGlobals, ToontownBattleGlobals
from game.toontown.estate import DistributedFlowerAI
from game.toontown.estate import DistributedGagTreeAI
from game.toontown.estate import DistributedStatuaryAI
from game.toontown.estate import DistributedGardenPlotAI
from game.toontown.estate import DistributedGardenBoxAI

import time, random

class DistributedEstateAI(DistributedObjectAI):
    notify = directNotify.newCategory('DistributedEstateAI')

    printedLs = 0

    EstateModel = None

    timeToEpoch = GardenGlobals.TIME_OF_DAY_FOR_EPOCH
    epochHourInSeconds = timeToEpoch * 60 * 60
    dayInSeconds = 24 * 60 * 60

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.houses = [None] * 6
        self.estateType = 0
        self.closestHouse = 0
        self.treasureIds = []
        self.dawnTime = 0
        self.decorData = []
        self.lastEpochTimeStamp = time.time()
        self.rentalType = 0
        self.clouds = 0
        self.cannons = []
        self.rentalTimeStamp = 0
        self.lawnItems = [[], [], [], [], [], []]
        self.idList = []
        self.spotPosHpr = [(49.1029, -124.805, 0.344704, 90, 0, 0),
                           (46.5222, -134.739, 0.390713, 75, 0, 0),
                           (41.31, -144.559, 0.375978, 45, 0, 0),
                           (46.8254, -113.682, 0.46015, 135, 0, 0)]
        self.pond = None
        self.treasurePlanner = None
        self.flyingTreasurePlanner = None
        self.fireworksCannon = None
        self.garden = None

        self.gardenList = [[],[],[],[],[],[]]
        self.gardenBoxList = [[],[],[],[],[],[]]

        self.accept('gardenTest', self.placeTestGarden)
        self.accept('gardenClear', self.clearMyGarden)
        self.accept('gardenNuke', self.nukeMyGarden)
        self.accept('gardenPlant', self.plantFlower)
        self.accept('wiltGarden', self.wiltMyGarden)
        self.accept('unwiltGarden', self.unwiltMyGarden)
        self.accept('waterGarden', self.setWaterLevelMyGarden)
        self.accept('growthGarden', self.setGrowthLevelMyGarden)
        self.accept('epochGarden', self.doEpochMagicWord)

        self.maxSlots = 32
        self.toonsPerAccount = 6
        #self.timePerEpoch = 300 #five minutes
        #self.timePerEpoch = 30000 #5000 minutes #NO LONGER A VALID CONCEPT AS EPOCHS HAPPEN ONCE A DAY
        self.gardenTable = []
        for count in range(self.toonsPerAccount):

            self.gardenTable.append([0] * self.maxSlots) #ACCOUNT HAS 6 TOONS

    def bootStrapEpochs(self):
        #first update the graden data based on how much time has based
        #print ("last time %s" % (self.lastEpochTimeStamp))
        currentTime = time.time()
        #print ("current time %s" % (currentTime))
        timeDiff = currentTime - self.lastEpochTimeStamp
        #print ("time diff %s" % (timeDiff))

        #self.lastEpochTimeStamp = time.mktime((2006, 8, 24, 10, 50, 31, 4, 237, 1))

        tupleNewTime = time.localtime(currentTime - self.epochHourInSeconds)
        tupleOldTime = time.localtime(self.lastEpochTimeStamp)

        if (tupleOldTime < time.gmtime(0)):
            tupleOldTime = time.gmtime(0)

        #tupleOldTime = (2006, 6, 18, 0, 36, 45, 0, 170, 1)
        #tupleNewTime = (2006, 6, 19, 3, 36, 45, 0, 170, 1)

        listLastDay = list(tupleOldTime)
        listLastDay[3] = 0 #set hour to epoch time
        listLastDay[4] = 0 #set minute to epoch time
        listLastDay[5] = 0 #set second to epoch time
        tupleLastDay = tuple(listLastDay)

        randomDelay = random.random() * 5 * 60 # random five minute range

        secondsNextEpoch = (time.mktime(tupleLastDay) + self.epochHourInSeconds + self.dayInSeconds + randomDelay) - currentTime


        #should we do the epoch for the current day?
        #beforeEpoch = 1
        #if  tupleNewTime[3] >= self.timeToEpoch:
        #    beforeEpoch = 0

        epochsToDo =  int((time.time() - time.mktime(tupleLastDay)) / self.dayInSeconds)
        #epochsToDo -= beforeEpoch
        if epochsToDo < 0:
            epochsToDo = 0

        print("epochsToDo %s" % (epochsToDo))

        #print("tuple times")
        #print tupleNewTime
        #print tupleOldTime


        if epochsToDo:
            pass
            print("doingEpochData")
            self.doEpochData(0, epochsToDo)
        else:
            pass
            print("schedualing next Epoch")
            #print("Delaying inital epoch")
            self.scheduleNextEpoch()
            self.sendUpdate("setLastEpochTimeStamp", [self.lastEpochTimeStamp])
            #time2Epoch = self.timePerEpoch - timeDiff

    def scheduleNextEpoch(self):
        currentTime = time.time()
        tupleNewTime = time.localtime()
        tupleOldTime = time.localtime(self.lastEpochTimeStamp)

        listLastDay = list(tupleOldTime)
        listLastDay[3] = 0 #set hour to epoch time
        listLastDay[4] = 0 #set minute to epoch time
        listLastDay[5] = 0 #set second to epoch time
        tupleLastDay = tuple(listLastDay)

        randomDelay = random.random() * 5 * 60 # random five minute range
        whenNextEpoch = (time.mktime(tupleLastDay) + self.epochHourInSeconds + self.dayInSeconds + randomDelay)
        secondsNextEpoch = whenNextEpoch - currentTime
        if secondsNextEpoch >= 0:
            secondsNextEpoch += self.dayInSeconds
        taskMgr.doMethodLater((secondsNextEpoch), self.doEpochNow, self.uniqueName("GardenEpoch"))

        tupleNextEpoch = time.localtime(whenNextEpoch)

        self.notify.info("Next epoch to happen at %s" % (str(tupleNextEpoch)))

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

        # Spawn our treasures:
        self.treasurePlanner = ETreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()

        # Generate our fishing pond:
        self.pond = DistributedFishingPondAI(self.air)
        self.pond.setArea(ToontownGlobals.MyEstate)
        self.pond.generateWithRequired(self.zoneId)
        self.pond.generateTargets()

        # Generate our fishing spots:
        for i in range(len(self.spotPosHpr)):
            spot = DistributedFishingSpotAI(self.air)
            spot.setPondDoId(self.pond.doId)
            spot.setPosHpr(*self.spotPosHpr[i])

            if not isinstance(spot, DistributedFishingSpotAI):
                self.notify.warning('Failed to generate spot for pond %d!' % self.pond.doId)
                continue

            spot.generateWithRequired(self.zoneId)
            self.pond.addSpot(spot)

        if simbase.wantPets:
            if 0:#__dev__:
                from pandac.PandaModules import ProfileTimer
                pt = ProfileTimer()
                pt.init('estate model load')
                pt.on()

            if not DistributedEstateAI.EstateModel:
                # load up the estate model for the pets
                self.dnaStore = DNAStorage()
                simbase.air.loadDNAFile(
                    self.dnaStore,
                    self.air.lookupDNAFileName('storage_estate.dna'))
                node = simbase.air.loadDNAFile(
                    self.dnaStore,
                    self.air.lookupDNAFileName('estate_1.dna'))
                DistributedEstateAI.EstateModel = hidden.attachNewNode(
                    node)
            render = self.getRender()
            self.geom = DistributedEstateAI.EstateModel.copyTo(render)
            # for debugging, show what's in the model
            if not DistributedEstateAI.printedLs:
                DistributedEstateAI.printedLs = 1
                #self.geom.ls()

            if 0:#__dev__:
                pt.mark('loaded estate model')
                pt.off()
                pt.printTo()

        if config.GetBool('want-fireworks-cannons', False):
            self.fireworksCannon = DistributedFireworksCannonAI(self.air)
            self.fireworksCannon.generateWithRequired(self.zoneId)

        self.garden = DistributedGardenAI(self.air)
        self.garden.generateWithRequired(self.zoneId)
        self.garden.sendNewProp(HouseGlobals.PROP_ICECUBE, 4.710, -86.550, 2.478)

    if simbase.wantPets:
        def createPetCollisions(self):
            # call this after the world geom is all set up
            render=self.getRender()
            # find the collisions and make copies of them, centered at Z=0
            self.petColls = render.attachNewNode('petColls')
            colls = self.geom.findAllMatches('**/+CollisionNode')
            for coll in colls:
                bitmask = coll.node().getIntoCollideMask()
                if not (bitmask & BitMask32(OTPGlobals.WallBitmask)).isZero():
                    newColl = coll.copyTo(self.petColls)
                    # make sure it's still in the correct position relative
                    # to the world
                    newColl.setTransform(coll.getTransform(self.geom))
                    """
                    bounds = coll.getBounds()
                    height = abs(bounds.getMax()[2] - bounds.getMin()[2])
                    """
                    # move down two feet to account for collisions that are
                    # not at Z=0
                    newColl.setZ(render, -2)
            self.geom.stash()
            # set up the collision traverser for this zone
            self.getZoneData().startCollTrav()

    def destroyEstateData(self):
        if hasattr(self, "Estate_deleted"):
            DistributedEstateAI.notify.debug("destroyEstateData: estate already deleted: %s" % self.Estate_deleted)
            return

        DistributedEstateAI.notify.debug("destroyEstateData: %s" % self.__dict__.get("zoneId"))

        #if hasattr(self, 'zoneId'):
        #    DistributedEstateAI.notify.debug('destroyEstateData: %s' % self.zoneId)
        #else:
        #    DistributedEstateAI.notify.debug('destroyEstateData: zoneID reference deleted')

        if hasattr(self, 'geom'):
            self.petColls.removeNode()
            del self.petColls
            self.geom.removeNode()
            del self.geom
            self.releaseZoneData()
        else:
            DistributedEstateAI.notify.debug('estateAI has no geom...')

    def setEstateType(self, estateType):
        self.estateType = estateType

    def d_setEstateType(self, estateType):
        self.sendUpdate('setEstateType', [estateType])

    def b_setEstateType(self, estateType):
        self.setEstateType(estateType)
        self.d_setEstateType(estateType)

    def getEstateType(self):
        return self.estateType

    def setClosestHouse(self, closestHouse):
        self.closestHouse = closestHouse

    def setTreasureIds(self, treasureIds):
        self.treasureIds = treasureIds

    def d_setTreasureIds(self, treasureIds):
        self.sendUpdate('setTreasureIds', [treasureIds])

    def b_setTreasureIds(self, treasureIds):
        self.setTreasureIds(treasureIds)
        self.d_setTreasureIds(treasureIds)

    def getTreasureIds(self):
        return self.treasureIds

    def requestServerTime(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        self.sendUpdateToAvatarId(avId, 'setServerTime', [time.time() % HouseGlobals.DAY_NIGHT_PERIOD])

    def setDawnTime(self, dawnTime):
        self.dawnTime = dawnTime

    def d_setDawnTime(self, dawnTime):
        self.sendUpdate('setDawnTime', [dawnTime])

    def b_setDawnTime(self, dawnTime):
        self.setDawnTime(dawnTime)
        self.d_setDawnTime(dawnTime)

    def getDawnTime(self):
        return self.dawnTime

    def placeOnGround(self, doId):
        self.sendUpdate('placeOnGround', [doId])

    def b_setDecorData(self, decorData):
        self.setDecorData(decorData)
        self.d_setDecorData(decorData)

    def setDecorData(self, decorData):
        self.decorData = decorData
        #print ("setDecorData %s" % (self.doId))

    def d_setDecorData(self, decorData):
        print("FIXME when correct toon.dc is checked in")
        #self.sendUpdate("setDecorData", [decorData])

    def getDecorData(self):
        if hasattr(self, "decorData"):
            return self.decorData
        else:
            return []

    def getLastEpochTimeStamp(self):
        return self.lastEpochTimeStamp

    def setLastEpochTimeStamp(self, ts):
        self.lastEpochTimeStamp = ts

    def saveTime(self):
        currentTime = time.time()
        self.setLastEpochTimeStamp(currentTime)
        self.sendUpdate("setLastEpochTimeStamp", [currentTime])

    def setRentalTimeStamp(self, rentalTimeStamp):
        self.rentalTimeStamp = rentalTimeStamp

    def d_setRentalTimeStamp(self, rentalTimeStamp):
        self.sendUpdate('setRentalTimeStamp', [rentalTimeStamp])

    def b_setRentalTimeStamp(self, rentalTimeStamp):
        self.setRentalTimeStamp(rentalTimeStamp)
        self.d_setRentalTimeStamp(rentalTimeStamp)

    def getRentalTimeStamp(self):
        return self.rentalTimeStamp

    def setRentalType(self, rentalType):
        self.rentalType = rentalType
        if rentalType:
            if time.time() >= self.rentalTimeStamp:
                self.b_setRentalType(0)
                self.b_setRentalTimeStamp(0)
                return

            if rentalType == ToontownGlobals.RentalCannon:
                target = DistributedTargetAI(self.air, -5.6, -24, 50)
                target.generateWithRequired(self.zoneId)
                target.start()
                self.cannons.append(target)
                for posHpr in CannonGlobals.cannonDrops:
                    cannon = DistributedCannonAI(self.air, self.doId, target.doId, *posHpr)
                    cannon.generateWithRequired(self.zoneId)
                    self.cannons.append(cannon)

                self.b_setClouds(1)
                self.flyingTreasurePlanner = EFlyingTreasurePlannerAI(self.zoneId, callback=self.__treasureGrabbed)
                self.flyingTreasurePlanner.placeAllTreasures()
                self.b_setTreasureIds([treasure.doId for treasure in self.flyingTreasurePlanner.treasures])

            taskMgr.doMethodLater(self.rentalTimeStamp - time.time(), self.__rentalExpire,
                                  self.uniqueName('rentalExpire'))

    def b_setRentalType(self, rentalType):
        self.setRentalType(rentalType)
        self.d_setRentalType(rentalType)

    def d_setRentalType(self, rentalType):
        self.sendUpdate('setRentalType', [rentalType])

    def __treasureGrabbed(self, _):
        self.b_setTreasureIds([treasure.doId for treasure in self.flyingTreasurePlanner.treasures if treasure])

    def __rentalExpire(self, task):
        if self.getRentalType() == ToontownGlobals.RentalCannon:
            for cannon in self.cannons[:]:
                cannon.requestDelete()
                self.cannons.remove(cannon)

            self.b_setClouds(0)
            self.b_setRentalTimeStamp(0)
            self.b_setRentalType(0)
            self.b_setTreasureIds([])
            self.flyingTreasurePlanner.deleteAllTreasuresNow()
            self.flyingTreasurePlanner = None

        return task.done

    def getRentalType(self):
        return self.rentalType

# lots of get and set functions, not really the prettiest way to do this but it works

    def getToonId(self, slot):
        if slot == 0:
            if hasattr(self, "slot0ToonId"):
                return self.slot0ToonId
        elif slot == 1:
            if hasattr(self, "slot1ToonId"):
                return self.slot1ToonId
        elif slot == 2:
            if hasattr(self, "slot2ToonId"):
                return self.slot2ToonId
        elif slot == 3:
            if hasattr(self, "slot3ToonId"):
                return self.slot3ToonId
        elif slot == 4:
            if hasattr(self, "slot4ToonId"):
                return self.slot4ToonId
        elif slot == 5:
            if hasattr(self, "slot5ToonId"):
                return self.slot5ToonId
        else:
            return None

    def setToonId(self, slot, tag):
        if slot == 0:
            self.slot0ToonId = tag
        elif slot == 1:
            self.slot1ToonId = tag
        elif slot == 2:
            self.slot2ToonId = tag
        elif slot == 3:
            self.slot3ToonId = tag
        elif slot == 4:
            self.slot4ToonId = tag
        elif slot == 5:
            self.slot5ToonId = tag

    def d_setToonId(self, slot, avId):
        if avId:
            if slot == 0:
                self.sendUpdate("setSlot0ToonId", [avId])
            elif slot == 1:
                self.sendUpdate("setSlot1ToonId", [avId])
            elif slot == 2:
                self.sendUpdate("setSlot2ToonId", [avId])
            elif slot == 3:
                self.sendUpdate("setSlot3ToonId", [avId])
            elif slot == 4:
                self.sendUpdate("setSlot4ToonId", [avId])
            elif slot == 5:
                self.sendUpdate("setSlot5ToonId", [avId])

    def b_setToonId(self, slot, avId):
        self.setToonId(slot, avId)
        self.d_setToonId(slot, avId)

    def getItems(self, slot):
        if slot == 0:
            if hasattr(self, "slot0Items"):
                return self.slot0Items
        elif slot == 1:
            if hasattr(self, "slot1Items"):
                return self.slot1Items
        elif slot == 2:
            if hasattr(self, "slot2Items"):
                return self.slot2Items
        elif slot == 3:
            if hasattr(self, "slot3Items"):
                return self.slot3Items
        elif slot == 4:
            if hasattr(self, "slot4Items"):
                return self.slot4Items
        elif slot == 5:
            if hasattr(self, "slot5Items"):
                return self.slot5Items
        else:
            return None

    def setOneItem(self, ownerIndex, hardPointIndex, gardenItemType=-1, waterLevel=None, growthLevel=-1, variety=-1):
        assert ownerIndex >= 0 and ownerIndex < 6
        itemList = self.getItems(ownerIndex)
        itemsIndex = self.findItemPositionInItemList(itemList, hardPointIndex)
        if itemsIndex != -1 and gardenItemType == -1:
            gardenItemType = itemList[itemsIndex][0]
        if itemsIndex != -1  and waterLevel == None:
            waterLevel = itemList[itemsIndex][2]
        if itemsIndex != -1  and growthLevel == -1:
            growthLevel = itemList[itemsIndex][3]
        if itemsIndex != -1  and variety == -1:
            variety = itemList[itemsIndex][4]
        newInfo = (gardenItemType, hardPointIndex, waterLevel, growthLevel, variety)
        #since itemList is a reference, just update it
        if itemsIndex != -1 :
            itemList[itemsIndex] = newInfo
        else:
            itemList.append(newInfo)

    # Note there is no d_setOneItem, since the whole itemList gets updated

    def b_setOneItem(self, ownerIndex, hardPointIndex, gardenItemType=-1,
                    waterLevel=-1, growthLevel=-1, variety=-1):
       """
       If you're changing multiple items, it's better to call b_setItems than
       multiple calls to b_setOneItem
       """
       self.setOneItem(ownerIndex, hardPointIndex, gardenItemType,
                       waterLevel, growthLevel, variety)
       self.d_setItems(ownerIndex, self.getItems(ownerIndex))

    def setItems(self, slot, items):
        if slot == 0:
            self.slot0Items = items
        elif slot == 1:
            self.slot1Items = items
        elif slot == 2:
            self.slot2Items = items
        elif slot == 3:
            self.slot3Items = items
        elif slot == 4:
            self.slot4Items = items
        elif slot == 5:
            self.slot5Items = items

    def d_setItems(self, slot, items):
        items = self.checkItems(items)
        if slot == 0:
            self.sendUpdate("setSlot0Items", [items])
        elif slot == 1:
            self.sendUpdate("setSlot1Items", [items])
        elif slot == 2:
            self.sendUpdate("setSlot2Items", [items])
        elif slot == 3:
            self.sendUpdate("setSlot3Items", [items])
        elif slot == 4:
            self.sendUpdate("setSlot4Items", [items])
        elif slot == 5:
            self.sendUpdate("setSlot5Items", [items])

    def checkItems(self, items, slot = 0):
        toonId = self.getToonId(slot)
        for item in items:
            if (item[0] < 0) or (item[1] < 0) or (item[4] < 0):
                self.air.writeServerEvent("Removing_Invalid_Garden_Item_on_Toon ", toonId, " item %s" % str(item))
                items.remove(item)
        return items

    def b_setItems(self, slot, items):
        items = self.checkItems(items)
        self.setItems(slot, items)
        self.d_setItems(slot, items)

    def setSlot0ToonId(self, avId):
        self.slot0ToonId = avId

    def setSlot1ToonId(self, avId):
        self.slot1ToonId = avId

    def setSlot2ToonId(self, avId):
        self.slot2ToonId = avId

    def setSlot3ToonId(self, avId):
        self.slot3ToonId = avId

    def setSlot4ToonId(self, avId):
        self.slot4ToonId = avId

    def setSlot5ToonId(self, avId):
        self.slot5ToonId = avId

    def setSlot0Items(self, items):
        self.slot0Items = items

    def setSlot1Items(self, items):
        self.slot1Items = items

    def setSlot2Items(self, items):
        self.slot2Items = items

    def setSlot3Items(self, items):
        self.slot3Items = items

    def setSlot4Items(self, items):
        self.slot4Items = items

    def setSlot5Items(self, items):
        self.slot5Items = items

    def getSlot0ToonId(self):
        if hasattr(self, "slot0ToonId"):
            return self.slot0ToonId
        else:
            return 0

    def getSlot1ToonId(self):
        if hasattr(self, "slot1ToonId"):
            return self.slot1ToonId
        else:
            return 0

    def getSlot2ToonId(self):
        if hasattr(self, "slot2ToonId"):
            return self.slot2ToonId
        else:
            return 0

    def getSlot3ToonId(self):
        if hasattr(self, "slot3ToonId"):
            return self.slot3ToonId
        else:
            return 0

    def getSlot4ToonId(self):
        if hasattr(self, "slot4ToonId"):
            return self.slot4ToonId
        else:
            return 0

    def getSlot5ToonId(self):
        if hasattr(self, "slot5ToonId"):
            return self.slot5ToonId
        else:
            return 0

    def getSlot0Items(self):
        if hasattr(self, "slot0Items"):
            return self.slot0Items
        else:
            return []

    def getSlot1Items(self):
        if hasattr(self, "slot1Items"):
            return self.slot1Items
        else:
            return []

    def getSlot2Items(self):
        if hasattr(self, "slot2Items"):
            return self.slot2Items
        else:
            return []

    def getSlot3Items(self):
        if hasattr(self, "slot3Items"):
            return self.slot3Items
        else:
            return []

    def getSlot4Items(self):
        if hasattr(self, "slot4Items"):
            return self.slot4Items
        else:
            return []

    def getSlot5Items(self):
        if hasattr(self, "slot5Items"):
            return self.slot5Items
        else:
            return []

    def completeFlowerSale(self, flag):
        if not flag:
            return

        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return

        collection = av.flowerCollection
        earning = 0
        newSpecies = 0
        for flower in av.flowerBasket.getFlower():
            if collection.collectFlower(flower) == GardenGlobals.COLLECT_NEW_ENTRY:
                newSpecies += 1

            earning += flower.getValue()

        av.b_setFlowerBasket([], [])
        av.d_setFlowerCollection(*av.flowerCollection.getNetLists())
        av.addMoney(earning)
        oldSpecies = len(collection) - newSpecies
        dt = abs(len(collection) // 10 - oldSpecies // 10)
        if dt:
            self.notify.info('%d is getting a gardening trophy!' % avId)
            maxHp = av.getMaxHp()
            maxHp = min(ToontownGlobals.MaxHpLimit, maxHp + dt)
            av.b_setMaxHp(maxHp)
            av.toonUp(maxHp)
            self.sendUpdate('awardedTrophy', [avId])

        av.b_setGardenTrophies(list(range(len(collection) // 10)))

    def setClouds(self, clouds):
        self.clouds = clouds

    def d_setClouds(self, clouds):
        self.sendUpdate('setClouds', [clouds])

    def b_setClouds(self, clouds):
        self.setClouds(clouds)
        self.d_setClouds(clouds)

    def getClouds(self):
        return self.clouds

    def rentItem(self, typeIndex, duration):
        self.b_setRentalTimeStamp(time.time() + duration * 60)
        self.b_setRentalType(typeIndex)

    def cannonsOver(self):
        pass  # TODO

    def gameTableOver(self):
        pass  # TODO

    def getAvHouse(self, avId):
        if not avId:
            return
        resp = None
        for house in self.houses:
            if house is not None:
                if house.getAvatarId() == avId:
                    return house

    def delete(self):
        if self.treasurePlanner:
            self.treasurePlanner.stop()
            self.treasurePlanner.deleteAllTreasuresNow()
            self.treasurePlanner = None

        if self.flyingTreasurePlanner:
            self.flyingTreasurePlanner.deleteAllTreasuresNow()
            self.flyingTreasurePlanner = None

        if self.pond is not None:
            self.pond.requestDelete()
            self.pond = None

        for cannon in self.cannons[:]:
            cannon.requestDelete()
            self.cannons.remove(cannon)

        if self.fireworksCannon:
            self.fireworksCannon.requestDelete()
            self.fireworksCannon = None

            self.deleteGarden()

            if hasattr(self,'gardenBoxList'):
                for index in range(len(self.gardenBoxList)):
                    for box in self.gardenBoxList[index]:
                        if box:
                            box.requestDelete()

            del self.gardenBoxList
            del self.gardenTable
            # del self.estateButterflies
            del self.gardenList

        taskMgr.remove(self.uniqueName('rentalExpire'))
        DistributedObjectAI.delete(self)

    def deleteGarden(self):
        if not hasattr(self,'gardenTable'):
            return

        print("calling delete garden")

        for index in range(len(self.gardenTable)):
            for distLawnDecor in self.gardenTable[index]:
                if distLawnDecor: # and distLawnDecor.occupied:
                    distLawnDecor.requestDelete()

        self.gardenTable = []

    def destroy(self):
        for house in self.houses:
            if house is not None:
                house.requestDelete()

        del self.houses[:]
        self.requestDelete()

    def doEpochNow(self, onlyForThisToonIndex):
        avId = self.idList[onlyForThisToonIndex]
        house = self.getAvHouse(avId)
        house.gardenManager.gardens.get(avId).growFlowers()

    def checkItems(self, items, slot = 0):
        toonId = self.getToonId(slot)
        for item in items:
            if (item[0] < 0) or (item[1] < 0) or (item[4] < 0):
                self.air.writeServerEvent("Removing_Invalid_Garden_Item_on_Toon ", toonId, " item %s" % str(item))
                items.remove(item)
        return items

    def b_setItems(self, slot, items):
        items = self.checkItems(items)
        self.setItems(slot, items)
        self.d_setItems(slot, items)

    def placeTestGarden(self, avId = 0):
        #print("placing test Items %s" % (avId))
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                self.clearGarden(index)
                self.b_setItems(index,[])
                self.placeLawnDecor(index, self.getItems(index))

                #mark the toon as 'garden started'
                toon = simbase.air.doId2do.get(avId)
                if toon:
                    toon.b_setGardenStarted(True)
                    #log that they are starting the garden
                    self.air.writeServerEvent("garden_started", self.doId, '')

    def placeStarterGarden(self, avId = 0):
        #print("placing test Items %s" % (avId))
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                #mark the toon as 'garden started'
                toon = simbase.air.doId2do.get(avId)
                if toon:
                    if not toon.getGardenStarted():
                        toon.b_setGardenStarted(True)
                        #log that they are starting the garden
                        self.air.writeServerEvent("garden_started", self.doId, '')

                if self.getItems(index) == [(255,0,-1,-1,0)]:
                    #case where the garden has been tagged as empty
                    self.clearGarden(index)
                    self.b_setItems(index,[])
                    self.placeLawnDecor(index, self.getItems(index))

    def clearGarden(self, slot):
        for entry in self.gardenTable[slot]:
            if entry and entry != 0:
                entry.requestDelete()
            entry = 0
        #self.gardenList[slot] = []

    def clearMyGarden(self, avId = 0):
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                for hardPoint in range(len(GardenGlobals.estatePlots[index])):
                    self.removePlantAndPlaceGardenPlot(index, hardPoint)
                #self.clearGarden(index)
                #self.b_setItems(index,[])

    def nukeMyGarden(self, avId = 0):
        for index in range(self.toonsPerAccount):
            if self.getToonId(index) == avId:
                for hardPoint in range(len(GardenGlobals.estatePlots[index])):
                    self.removePlant(index, hardPoint)
                    self.removeGardenPlot(index,hardPoint)
                for box in self.gardenBoxList[index]:
                    box.requestDelete()
                self.gardenBoxList[index] = []

                self.b_setItems(index, [(255,0,-1,-1,0)]) #empty garden tag

    def gardenInit(self, avIdList):
        self.sendUpdate('setIdList', [avIdList])
        #self.bootStrapEpochs()


        self.avIdList = avIdList
        #check to see if the av field tags match the house owners
        for index in range(len(avIdList)):
            if self.getToonId(index) != avIdList[index]:
                self.notify.debug("Mismatching Estate Tag index %s id %s list %s" % (index, self.getToonId(index) , avIdList[index]))
            if self.getItems(index) == None:
                self.notify.debug("Items is None index %s items %s" % (index, self.getItems(index)))
            if self.getToonId(index) != avIdList[index] or self.getItems(index) == None:
                self.notify.debug("Resetting items index %s" % (index))
                self.b_setToonId(index, avIdList[index])
                #resetting the item database
                #self.b_setItems(index, [])
                self.b_setItems(index, [(255,0,-1,-1,0)]) #empty garden tag
            if self.getItems(index) == [(255,0,-1,-1,0)]:
                #case where the garden has been tagged as empty
                pass
            elif self.getItems(index) or self.getItems(index) == []:
                self.placeLawnDecor(index, self.getItems(index))
                #print "Item Check"
                #print self.getItems(index)
                pass
            self.updateToonBonusLevels(index)
        self.bootStrapEpochs()
        #self.b_setItems(1,[[49,0,16,16,0]])#get some data up for testing

    def updateToonBonusLevels(self, index):
        # find the trees with fruit
        numTracks = len(ToontownBattleGlobals.Tracks)
        hasBonus = [[] for n in range(numTracks)]
        for distLawnDecor in self.gardenTable[index]:
            # keep track of which trees are blooming
            if distLawnDecor and distLawnDecor.hasGagBonus():
                hasBonus[distLawnDecor.gagTrack].append(distLawnDecor.gagLevel)

        # find the lowest gaglevel for each track that immediately preceeds a non-fruited tree
        # EG.  [0, 1, 2, 4, 5, 6] should find 2
        bonusLevels = [-1] * len(ToontownBattleGlobals.Tracks)
        for track in range(len(hasBonus)):
            hasBonus[track].sort()
            for gagLevel in hasBonus[track]:
                if gagLevel == (bonusLevels[track] + 1):
                    bonusLevels[track] = gagLevel
                else:
                    break

        # tell the toon
        toonId = self.getToonId(index)
        toon = simbase.air.doId2do.get(toonId)
        if toon:
            toon.b_setTrackBonusLevel(bonusLevels)

    def plantFlower(self, avId, type, plot, water, growth, optional = 0):
            for index in range(self.toonsPerAccount):
                if self.getToonId(index) == avId:
                    self.removePlant(index, plot)
                    itemId = self.addLawnDecorItem(index, type, plot, water, growth,optional)
                    itemList = self.getItems(index)
                    itemList.append((type, plot, water, growth, optional))
                    self.b_setItems(index, itemList)
            return itemId

    def plantTree(self, avId, type, plot, water, growth, optional = 0):
            for index in range(self.toonsPerAccount):
                if self.getToonId(index) == avId:
                    self.removePlant(index, plot)
                    itemDoId = self.addLawnDecorItem(index, type, plot, water, growth,optional)
                    itemList = self.getItems(index)
                    itemList.append((type, plot, water, growth, optional))
                    self.b_setItems(index, itemList)
            return itemDoId

    def removePlant(self, slot, plot):
        itemList = self.getItems(slot)
        for item in self.getItems(slot):
            if item[1] == plot:
                if self.gardenTable[slot][plot]:
                    self.gardenTable[slot][plot].requestDelete()
                    self.gardenTable[slot][plot] = None
                itemList.remove(item)
                #we need to do a b_setItems to save the change in database
                self.b_setItems(slot, itemList)
                self.updateToonBonusLevels(slot)

    def addLawnDecorItem(self, slot, type, hardPoint, waterLevel, growthLevel, optional = 0):
            #Hard coding MickeyStatue1 to be my toon statue
            plantClass = DistributedFlowerAI.DistributedFlowerAI
            plantType = GardenGlobals.PlantAttributes[type]['plantType']
            if plantType == GardenGlobals.GAG_TREE_TYPE:
                #print("print")
                plantClass = DistributedGagTreeAI.DistributedGagTreeAI
                testPlant = DistributedGagTreeAI.DistributedGagTreeAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                postion = GardenGlobals.estatePlots[slot][hardPoint]
                testPlant.setPosition(postion[0], postion[1], 0)
                testPlant.setH(postion[2])
            elif plantType == GardenGlobals.FLOWER_TYPE:
                #print("FLOWER")
                plantClass =  DistributedFlowerAI.DistributedFlowerAI
                testPlant = DistributedFlowerAI.DistributedFlowerAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                plot = GardenGlobals.estatePlots[slot][hardPoint]
                #postion = GardenGlobals.estateBoxes[slot][plot[0]]
                postion = self.gardenBoxList[slot][plot[0]].getBoxPos(plot[1])
                heading = self.gardenBoxList[slot][plot[0]].getH()
                testPlant.setPosition(postion[0], postion[1], postion[2])
                testPlant.setH(heading)
            elif plantType == GardenGlobals.STATUARY_TYPE:
                #print("STATUARY")
                plantClass = DistributedStatuaryAI.DistributedStatuaryAI
                if type in GardenGlobals.ToonStatuaryTypeIndices:
                    # Some hardcoded optional values for testing
                    # optional = 2325 #Pig = 3861 #Bear = 3349 #Monkey = 2837 #Duck = 2325 #Rabbit = 1813 #Mouse = 1557 #Horse = 1045 #Cat = 533 #Dog = 21
                    testPlant = DistributedToonStatuaryAI.DistributedToonStatuaryAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                elif type in GardenGlobals.ChangingStatuaryTypeIndices:
                    testPlant = DistributedChangingStatuaryAI.DistributedChangingStatuaryAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                else:
                    testPlant = DistributedStatuaryAI.DistributedStatuaryAI(type, waterLevel, growthLevel, optional, slot, hardPoint)
                postion = GardenGlobals.estatePlots[slot][hardPoint]
                testPlant.setPosition(postion[0], postion[1], 0)
                testPlant.setH(postion[2])

            testPlant.generateWithRequired(self.zoneId)
            testPlant.setEstateId(self.doId)

            #print ("Placing at Position %s %s %s" % (postion[0], postion[1], postion[2]))
            #self.placeOnGround(testPlant.doId)
            self.gardenTable[slot][hardPoint] = testPlant
            self.notify.debug('testPlant.doId : %s' %testPlant.doId)
            return testPlant.doId

    def placeLawnDecor(self, toonIndex, itemList):
        boxList = GardenGlobals.estateBoxes[toonIndex]
        for boxPlace in boxList:
            newBox = DistributedGardenBoxAI.DistributedGardenBoxAI(boxPlace[3])
            newBox.setPosition(boxPlace[0], boxPlace[1], 16)
            newBox.setH(boxPlace[2])
            newBox.generateWithRequired(self.zoneId)
            newBox.setEstateId(self.doId)
            newBox.setupPetCollision()
            self.gardenBoxList[toonIndex].append(newBox)
        plotList = GardenGlobals.estatePlots[toonIndex]
        for plotPointIndex in (range(len(plotList))):
            item = self.findItemAtHardPoint(itemList, plotPointIndex)
            if not item or not GardenGlobals.PlantAttributes.get(item[0]):
                item = None
            if item:
                type = item[0]
                if type not in GardenGlobals.PlantAttributes.keys():
                    self.notify.warning('type %d not found in PlantAttributes, forcing it to 48' % type)
                    type = 48
                hardPoint = item[1]
                waterLevel = item[2]
                growthLevel = item[3]
                optional = item[4] #all fields are 8bit except optional which is 16bits
                itemdoId = self.addLawnDecorItem(toonIndex, type, hardPoint, waterLevel, growthLevel, optional)
            else:
                #pass
                self.addGardenPlot(toonIndex, plotPointIndex)

    def addGardenPlot(self, slot, hardPoint):

            #print("HARDPOINT")
            plot = GardenGlobals.estatePlots[slot][hardPoint]
            #print(plot)
            if plot[3] == GardenGlobals.FLOWER_TYPE:
                #print("flower type")
                postion = self.gardenBoxList[slot][plot[0]].getBoxPos(plot[1])
                heading = self.gardenBoxList[slot][plot[0]].getH()
            else:
                #print("not flower type")
                postion = plot
                heading = postion[2]
            plantClass = DistributedGardenPlotAI.DistributedGardenPlotAI
            testPlant = DistributedGardenPlotAI.DistributedGardenPlotAI(plot[2], slot, hardPoint)
            testPlant.setPosition(postion[0], postion[1], 16)
            testPlant.setH(heading)
            testPlant.generateWithRequired(self.zoneId)

            #print ("Placing at Position %s %s" % (postion[0], postion[1]))
            self.placeOnGround(testPlant.doId)
            self.gardenTable[slot][hardPoint] = testPlant
            return testPlant.doId

    def removeGardenPlot(self, slot, plot):
        if self.gardenTable[slot][plot]:
            self.gardenTable[slot][plot].requestDelete()
            self.gardenTable[slot][plot] = None

    def findItemAtHardPoint(self, itemList, hardPoint):
        for item in itemList:
            if hardPoint == item[1]:
                return item
        return None

    def doEpochData(self, time, numEpochs = 0, onlyForThisToonIndex = None):
        #this function just updates the data buit doesn't effect anything within the zone
        self.saveTime()

        # Tell the distributedLawnDecors to update themselves... and update our 'itemLists'
        #numEpochs = int(time / self.timePerEpoch)
        #print ("Epochs passed %d" % (numEpochs))
        #do the epoch based stuff here like growing, consuming water, etc....


        for index in range(len(self.gardenTable)):
            anyUpdates = False
            numWilted = 0
            numHealthy = 0
            for distLawnDecor in self.gardenTable[index]:
                if distLawnDecor and distLawnDecor.occupied:
                    if onlyForThisToonIndex and \
                       not distLawnDecor.getOwnerIndex() == onlyForThisToonIndex:
                        #print("passing for this toon")
                        continue
                    anyUpdates = True
                    #print("doing epoch %s" % (numEpochs))
                    distLawnDecor.doEpoch(numEpochs)

                    if hasattr(distLawnDecor, 'isWilted'):
                        if distLawnDecor.isWilted():
                            numWilted += 1
                        else:
                            numHealthy += 1
                else:
                    pass
                    #print("PROBLEM %s %s" % (distLawnDecor, distLawnDecor.occupied))


            if numHealthy or numWilted:
                #log how many healthy and wilted plants he has after these epochs have been run
                self.air.writeServerEvent('garden_epoch_run', self.getToonId(index),
                                          '%d|%d|%d' % (numEpochs, numHealthy, numWilted))


            if anyUpdates:
                self.b_setItems(index, self.getItems(index))
                self.updateToonBonusLevels(index)

        self.scheduleNextEpoch()
        #taskMgr.doMethodLater(self.timePerEpoch, self.doEpochNow, self.uniqueName("GardenEpoch"))

    def hasGagTree(self, ownerIndex, gagTrack, gagLevel):
        """Return true if a gag tree is already planted on the estate that matches paremeters."""
        for distLawnDecor in self.gardenTable[ownerIndex]:
            if hasattr(distLawnDecor, 'gagTrack') and hasattr(distLawnDecor, 'gagLevel'):
                if distLawnDecor.gagTrack == gagTrack and \
                   distLawnDecor.gagLevel == gagLevel:
                    return True
        return False
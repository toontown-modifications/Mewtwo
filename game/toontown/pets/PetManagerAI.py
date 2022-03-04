from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.pets import PetDNA, PetMood, PetTraits, PetUtil
from game.toontown.pets.PetNameGenerator import PetNameGenerator

import json, os, random, string, time

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

def getDayId():
    return int(time.time() // DAY)

class PetManagerAI:
    notify = directNotify.newCategory('PetManagerAI')
    cachePath = config.GetString('air-pet-cache', 'backups/pets/')

    def __init__(self, air):
        self.air = air
        self.cacheFile = f'{self.cachePath}pets_{self.air.districtId}.pets'

        if not os.path.exists(self.cachePath):
            os.makedirs(self.cachePath)

        if os.path.isfile(self.cacheFile):
            with open(self.cacheFile, 'rb') as f:
                data = f.read()

            try:
                self.seeds = json.loads(data)
            except ValueError:
                self.seeds = {}

            if self.seeds.get('day', -1) != getDayId():
                self.seeds = {}
        else:
            self.seeds = {}

        self.nameGenerator = PetNameGenerator()

    def getAvailablePets(self, firstNumPets, secondNumPets):
        numPets = firstNumPets + secondNumPets

        if not self.seeds.get(str(numPets), []) or self.seeds.get('day', -1) != getDayId():
            self.seeds[str(numPets)] = random.sample(range(256), numPets)
            self.updatePetSeedCache()

        return self.seeds.get(str(numPets), [numPets])[0:numPets]

    def updatePetSeedCache(self):
        self.seeds['day'] = getDayId()

        with open(self.cacheFile, 'w') as f:
            f.write(json.dumps(self.seeds))

    def createNewPetFromSeed(self, avId, seed, nameIndex, gender, safeZoneId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        petName = self.nameGenerator.getName(nameIndex)
        _, dna, traitSeed = PetUtil.getPetInfoFromSeed(seed, safeZoneId)
        traits = PetTraits.PetTraits(traitSeed, safeZoneId)
        head, ears, nose, tail, body, color, colorScale, eyes, _ = dna
        numGenders = len(PetDNA.PetGenders)
        gender %= numGenders
        fields = {'setOwnerId': avId, 'setPetName': petName, 'setTraitSeed': traitSeed, 'setSafeZone': safeZoneId,
                  'setHead': head, 'setEars': ears, 'setNose': nose, 'setTail': tail, 'setBodyTexture': body,
                  'setColor': color, 'setColorScale': colorScale, 'setEyeColor': eyes, 'setGender': gender,
                  'setLastSeenTimestamp': int(time.time()), 'setTrickAptitudes': []}

        for traitName in PetTraits.getTraitNames():
            setter = 'set%s%s' % (traitName[0].upper(), traitName[1:])
            fields[setter] = traits.getTraitValue(traitName)

        for component in PetMood.PetMood.Components:
            setter = 'set%s%s' % (component[0].upper(), component[1:])
            fields[setter] = 0.0

        def petCreated(petId):
            if not petId:
                self.notify.warning('Cannot create pet for %s!' % avId)
                return

            self.air.writeServerEvent('bought-pet', avId = avId, petId = petId)
            av.b_setPetId(petId)

        self.air.dbInterface.createObject(self.air.dbId, self.air.dclassesByName['DistributedPetAI'],
                                          {key: (value,) for key, value in list(fields.items())}, petCreated)

    def deleteToonsPet(self, avId):
        av = self.air.doId2do.get(avId)

        if not av:
            return

        petId = av.getPetId()
        pet = self.air.doId2do.get(petId)

        if pet:
            pet.requestDelete()

        av.b_setPetId(0)
        self.air.writeServerEvent('returned-pet', avId = avId, petId = petId)
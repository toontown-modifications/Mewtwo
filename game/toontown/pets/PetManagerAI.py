from direct.directnotify.DirectNotifyGlobal import directNotify

from game.toontown.pets import PetDNA, PetMood, PetTraits, PetUtil
from game.toontown.pets.PetNameGenerator import PetNameGenerator

import time

class PetManagerAI:
    notify = directNotify.newCategory('PetManagerAI')

    def __init__(self, air):
        self.air = air

        self.nameGenerator = PetNameGenerator()

    def getAvailablePets(self, numDaysPetAvailable, numPetsPerDay):
        """
        This should get called when we first enter the PetChooser.
        It creates the list of toons that are available here.
        """

        from libsunrise import random
        import time
        S = random.getstate()

        curDay = int(time.time() / 60.0 / 60.0 / 24.0)
        seedMax = 2 ** 30  # or something like that
        seeds = []

        # get a seed for each day
        for i in range(numDaysPetAvailable):
            random.seed(curDay + i)
            # get a seed for each pet
            for j in range(numPetsPerDay):
                seeds.append(random.randrange(seedMax))

        return seeds

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
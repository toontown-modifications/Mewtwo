from game.toontown.hood import ZoneUtil
from game.toontown.toonbase import ToontownGlobals

def genDNAFileName(zoneId):
    zoneId = ZoneUtil.getCanonicalZoneId(zoneId)
    hoodId = ZoneUtil.getCanonicalHoodId(zoneId)
    hood = ToontownGlobals.dnaMap[hoodId]
    phase = ToontownGlobals.streetPhaseMap[hoodId]

    if hoodId == zoneId:
        zoneId = 'sz'

    return 'phase_{0}/dna/{1}_{2}.dna'.format(phase, hood, zoneId)

def extractGroupName(groupFullName):
    return groupFullName.split(':', 1)[0]
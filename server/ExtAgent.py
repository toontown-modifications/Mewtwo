from direct.distributed.PyDatagram import *
from direct.distributed.MsgTypes import *
from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.makeatoon.NameGenerator import NameGenerator
from game.toontown.toon.ToonDNA import ToonDNA
from OtpDoGlobals import *
from game.otp.otpbase import OTPGlobals
from game.toontown.toonbase import TTLocalizer
from game.toontown.hood import ZoneUtil
from game.toontown.toonbase import ToontownGlobals
from panda3d.toontown import DNAStorage, loadDNAFileAI
from game import genDNAFileName, extractGroupName
import json, time, os, random

ESSENTIAL_COMPLETE_ZONES = [
    OTP_ZONE_ID_OLD_QUIET_ZONE, 
    OTP_ZONE_ID_MANAGEMENT, 
    OTP_ZONE_ID_DISTRICTS,
    OTP_ZONE_ID_DISTRICTS_STATS,
    OTP_ZONE_ID_ELEMENTS
]

PERMA_ZONES = [
    OTP_ZONE_ID_OLD_QUIET_ZONE,
    OTP_ZONE_ID_DISTRICTS,
    OTP_ZONE_ID_DISTRICTS_STATS,
    OTP_ZONE_ID_MANAGEMENT
]

class JSONBridge:

    def __init__(self):
        self.__bridgeFile = config.GetString('account-bridge-file', 'otpd/databases/accounts.json')

        if not os.path.exists(self.__bridgeFile):
            self.__bridge = {}
        else:
            with open(self.__bridgeFile, 'r') as f:
                self.__bridge = json.load(f)

    def __save(self):
        """
        Save the bridge to the file.
        """

        with open(self.__bridgeFile, 'w+') as f:
            json.dump(self.__bridge, f)

    def put(self, playToken, accountId):
        """
        Throw an Account ID by its play token into the bridge.
        """

        self.__bridge[playToken] = accountId
        self.__save()

    def query(self, playToken):
        """
        Return the Account ID from the play token if it exists in the bridge.
        Otherwise, return False.
        """

        if playToken in self.__bridge:
            return self.__bridge[playToken]
        else:
            return False

class InterestManager(object):

    def __init__(self):
        self._interest_zones = []
        self._interest_objects = []

    @property
    def interest_zones(self):
        return self._interest_zones

    def has_interest_zone(self, zone_id):
        return zone_id in self._interest_zones

    def add_interest_zone(self, zone_id):
        if zone_id in self._interest_zones:
            return

        self._interest_zones.append(zone_id)

    def remove_interest_zone(self, zone_id):
        if zone_id not in self._interest_zones:
            return

        self._interest_zones.remove(zone_id)

    def clear(self):
        self._interest_zones = []

    def add_interest_object(self, i):
        self._interest_objects.append(i)

    def has_interest_object(self, i):
        return i in self._interest_objects

    def has_interest_object_id(self, _id, _obj = False):
        for interest in self._interest_objects:
            if interest.getId() == _id:
                if _obj:
                    return interest
                    
                return True
                
        return False

    def has_interest_object_parent(self, parentId):
        for interest in self._interest_objects:
            if interest.getParent() == parentId:
                return True
                
        return False

    def hasInterestObjectZone(self, zoneId):
        for interest in self._interest_objects:
            if interest.hasZone(zoneId) or interest.hasView(zoneId):
                return True

        return False

    def has_interest_object_parent_and_zone(self, parentId, zoneId, getObj = False, includeViews = False):
        for interest in self._interest_objects:
            if interest.getParent() == parentId and (interest.hasZone(zoneId) or (includeViews and interest.hasView(zoneId))):
                if getObj:
                    return interest
                return True

        return False

    def get_interest_object_by_id(self, _id):
        return self.has_interest_object_id(_id, True)

    def remove_interest_object(self, i):
        self._interest_objects.remove(i)

    def get_interest_objects(self):
        return self._interest_objects

class InterestOperation:
    def __init__(self, client, timeout, Id, context,  parent, zones, caller):

        self.client = client
        self.timeout = timeout
        self.id = Id
        self.context = context
        self.parent = parent
        self.zones = zones
        self.caller = caller

class ZoneList:

    def __init__(self):
        self.zones = []

    def addZone(self, zoneId):
        self.zones.append(zoneId)

    def removeZone(self, zoneId):
        self.zones.remove(zoneId)

    def getZones(self):
        return self.zones

    def hasZone(self, zoneId):
        return zoneId in self.zones

class Interest:

    def __init__(self):
        self.zones = ZoneList()
        self.visZones = set()
        self.id = -1
        self.context = -1
        self.parent = -1

    def setId(self, _id):
        self.id = _id

    def getId(self):
        return self.id

    def setContext(self, _context):
        self.context = _context

    def getContext(self):
        return self.context

    def setParent(self, _parent):
        self.parent = _parent

    def getParent(self):
        return self.parent

    def addZone(self, zone):
        self.zones.addZone(zone)

    def removeZone(self, zone):
        self.zones.removeZone(zone)

    def getZones(self):
        return self.zones.getZones()

    def hasZone(self, zone):
        return self.zones.hasZone(zone)

    def setVisZones(self, zones):
        self.visZones = zones

    def getVisZones(self):
        return self.visZones

    def hasView(self, zone):
        return zone in self.visZones

class VisibleObject:
    def __init__(self):
        self.parent = -1
        self.zone = -1
        self.id = -1

    def setParent(self, parent):
        self.parent = parent

    def getParent(self):
        return self.parent

    def setZone(self, zone):
        self.zone = zone

    def getZone(self):
        return self.zone

    def setId(self, _id):
        self.id = id

    def getId(self):
        return self.id

class DeferredCallback(object):
    """
    A class that represents a pending callback event when called
    it initiates the callback event with the specified arguments
    """

    def __init__(self, function, *args, **kwargs):
        assert(callable(function))
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def callback(self, *args, **kwargs):
        cb_args = []
        cb_args.extend(args)
        cb_args.extend(self._args)

        cb_kwargs = dict(kwargs.items() + self._kwargs.items())

        result = self._function(*cb_args, **cb_kwargs)

        del cb_args
        del cb_kwargs

        return result

    def destroy(self):
        self._function = None
        self._args = None
        self._kwargs = None

class ExtAgent:
    notify = directNotify.newCategory('ExtAgent')

    def __init__(self, air):
        self.air = air
        self.air.registerForChannel(5536)

        self.air.netMessenger.register(0, 'registerShard')
        self.air.netMessenger.accept('registerShard', self, self.registerShard)

        self.shardInfo = {}

        self.nameGenerator = NameGenerator()
        self.bridge = JSONBridge()

        self.loadAvProgress = set()

        self.clientChannel2avId = {}
        self.clientChannel2shardId = {}
        self.clientChannel2context = {}
        self.clientChannel2contextZone = {}

        self.interestManager = InterestManager()

        self.pendingInterests = {}
        self.seenObjects = {}
        self.ownedObjects = []
        self.dnaStores = {}

        self.deletedObjectHistory = []

        self.deferredCallback = None

    def sendEject(self, clientChannel, errorCode, errorStr):
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_EJECT)
        dg.addUint16(errorCode)
        dg.addString(errorStr)
        self.air.send(dg)

    def registerShard(self, shardId, shardName):
        self.shardInfo[shardId] = (shardName, 0)

    def loginAccount(self, fields, clientChannel, accountId, playToken):
        # If somebody is logged into this account, disconnect them.
        self.sendEject(self.air.GetAccountConnectionChannel(accountId), 100, 'This account has been logged into elsewhere.')

        # Wait half a second before continuing to avoid a race condition.
        taskMgr.doMethodLater(0.5,
                              lambda x: self.finishLoginAccount(fields, clientChannel, accountId, playToken),
                              self.air.uniqueName('wait-acc-%s' % accountId), appendTask=False)

    def finishLoginAccount(self, fields, clientChannel, accountId, playToken):
        # If there's anybody on the account, kill them for redundant login:
        datagram = PyDatagram()
        datagram.addServerHeader(self.air.GetAccountConnectionChannel(accountId), self.air.ourChannel, CLIENTAGENT_EJECT)
        datagram.addUint16(100)
        datagram.addString('This account has been logged in from elsewhere.')
        self.air.send(datagram)

        # Add the connection to the account channel.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
        dg.addChannel(self.air.GetAccountConnectionChannel(accountId))
        self.air.send(dg)

        # Set the client channel to the account ID shifted 32 bits to the left.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
        dg.addChannel(accountId << 32)
        self.air.send(dg)

        # Un-sandbox the client.
        self.air.setClientState(clientChannel, 2)

        wantAvMembership = config.GetBool('want-av-membership', False)

        # Prepare the login response.
        resp = PyDatagram()
        resp.addUint16(126) # CLIENT_LOGIN_TOONTOWN_RESP
        resp.addUint8(0)
        resp.addString('All Ok')
        resp.addUint32(1)
        resp.addString(playToken)
        resp.addUint8(1)
        resp.addString('YES')
        resp.addString('YES')
        resp.addString('YES')
        resp.addUint32(int(time.time()))
        resp.addUint32(int(time.clock()))

        if wantAvMembership:
            resp.addString('FULL')
        else:
            resp.addString('unpaid')

        resp.addString('YES')
        resp.addString(time.strftime('%Y-%m-%d %I:%M:%S'))
        resp.addInt32(1000 * 60 * 60)
        resp.addString('NO_PARENT_ACCOUNT')
        resp.addString(playToken)

        # Dispatch the response to the client.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)
    
    def lookupInterest(self, parent, zone):
        interests = []

        for interest in self.interestManager.get_interest_objects():
            if interest.getParent() == parent and interest.hasZone(zone):
                interests.append(interest)

        return interests

    def buildInterest(self, dgi):
        interestId = dgi.getUint16()
        contextId = dgi.getUint32()
        parentId = dgi.getUint32()

        interest = Interest()
        interest.setId(interestId)
        interest.setParent(parentId)
        interest.setContext(contextId)

        while dgi.getRemainingSize() > 0:
            interest.addZone(dgi.getUint32())

        return interest

    def handleInterestDone(self, clientChannel, interestId, context):
        resp = PyDatagram()

        resp.addUint16(48) # CLIENT_DONE_INTEREST_RESP

        resp.addUint16(interestId)
        resp.addUint32(context)

        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)

    def handleInterestCompleteCallback(self, clientChannel, complete, contextId):
        if complete:
            if contextId in self.pendingInterests:
                interest = self.pendingInterests[contextId]
                self.handleInterestDone(clientChannel, interest.id, contextId)
                del self.pendingInterests[contextId]
        else:
            if contextId in self.pendingInterests:
                interest = self.pendingInterests[contextId]
                zone = interest.getZones()[-1]
                self.notify.info(zone)
                if zone in self.seenObjects.keys():
                    self.handleInterestDone(clientChannel, interest.id, contextId)

    def closeZones(self, clientChannel, killZones, parent):
        # send delete for all objects we've seen that were in the zone
        # that we've just left...
        for zone in killZones:
            if zone not in PERMA_ZONES and zone in self.seenObjects:
                seenObjects = self.seenObjects[zone]
                for doId in seenObjects:
                    # we do not want to delete our owned objects...
                    if doId not in self.ownedObjects:
                        self.sendClientObjectDeleteResp(clientChannel, doId)

                del self.seenObjects[zone]

                # Tell the Client to disable the object.
                resp = PyDatagram()
                resp.addServerHeader(parent, clientChannel, CLIENT_OBJECT_DISABLE)

                resp.addUint32(zone)

                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)

                dg.addString(resp.getMessage())

                self.air.send(dg)

    def getInStreetBranch(self, zoneId):
        if not ZoneUtil.isPlayground(zoneId):
            where = ZoneUtil.getWhereName(zoneId, True)
            return where == 'street'

        return False

    def getInCogHQ(self, zoneId):
        if ZoneUtil.isCogHQZone(zoneId):
            return True

        return False

    def getVisBranchZones(self, zoneId, isCogHQ = False):
        branchZoneId = ZoneUtil.getBranchZone(zoneId)
        dnaStore = self.dnaStores.get(branchZoneId)

        if zoneId in (6100, 6101, 19000, 19001):
            # This is ToonLand.
            return []

        if zoneId in (ToontownGlobals.SellbotLobby, ToontownGlobals.LawbotOfficeExt, ToontownGlobals.LawbotLobby, ToontownGlobals.BossbotHQ, ToontownGlobals.CashbotLobby):
            return []

        if not dnaStore:
            dnaStore = DNAStorage()
            dnaFileName = genDNAFileName(branchZoneId)
            loadDNAFileAI(dnaStore, dnaFileName)
            self.dnaStores[branchZoneId] = dnaStore

        zoneVisDict = {}

        for i in xrange(dnaStore.getNumDNAVisGroupsAI()):
            groupFullName = dnaStore.getDNAVisGroupName(i)
            visGroup = dnaStore.getDNAVisGroupAI(i)
            visZoneId = int(extractGroupName(groupFullName))
            visZoneId = ZoneUtil.getTrueZoneId(visZoneId, zoneId)
            visibles = []

            for i in xrange(visGroup.getNumVisibles()):
                visibles.append(int(visGroup.getVisibleName(i)))

            visibles.append(ZoneUtil.getBranchZone(visZoneId))
            zoneVisDict[visZoneId] = visibles

        if not isCogHQ:
            return zoneVisDict[zoneId]
        else:
            return zoneVisDict.values()[0]

    def sendClientObjectDeleteResp(self, clientChannel, doId):
        # if the object is in the list of owned objects, we do not want to
        # delete this object, as it was already generated elsewhere...
        if doId in self.ownedObjects:
            return

        # only delete the object if we've previously seen the objects
        # generate request sent by the StateServer...
        if not self.hasSeenObject(doId, True):
            return

        # double check to prevent sending this more than one time
        if doId in self.deletedObjectHistory:
            return

        self.deletedObjectHistory.append(doId)

        resp = PyDatagram()

        resp.addUint16(CLIENT_OBJECT_DELETE_RESP)

        resp.addUint32(doId)

        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)

        dg.addString(resp.getMessage())

        self.air.send(dg)

    def hasSeenObject(self, doId, erase = False):
        for zoneId, seenObjects in list(self.seenObjects.items()):
            if doId in seenObjects:
                if erase:
                    self.seenObjects[zoneId].remove(doId)
                return True

        return False

    def handleDatagram(self, dgi):
        """
        This handles datagrams coming directly from the Toontown 2013 client.
        These datagrams may be reformatted in a way that can appease Astron,
        or are totally game-specific and will have their own handling.
        """

        clientChannel = dgi.getUint64()
        msgType = dgi.getUint16()

        if msgType == 3: # CLIENT_GET_AVATARS

            def handleAvRetrieveDone(avList, avatarFields):
                # Prepare the potential avatar datagram for the client.
                resp = PyDatagram()
                resp.addUint16(5) # CLIENT_GET_AVATARS_RESP
                resp.addUint8(0)
                resp.addUint16(len(avatarFields))

                for avId, fields in avatarFields.iteritems():
                    # Get the basic avatar fields the client needs.
                    index = avList.index(avId)
                    wishName = ''
                    wishNameState = fields.get('WishNameState', [''])[0]
                    name = fields['setName'][0]
                    allowedName = 0
                    if wishNameState == 'OPEN':
                        allowedName = 1
                    elif wishNameState == 'APPROVED':
                        name = fields['WishName'][0]
                    elif wishNameState == 'REJECTED':
                        allowedName = 1

                    resp.addUint32(avId)
                    resp.addString(name)
                    resp.addString('')
                    resp.addString('')
                    resp.addString('')
                    resp.addString(fields['setDNAString'][0])
                    resp.addUint8(index)
                    resp.addUint8(0)

                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['AccountUD']:
                    # The Account object could not be located.
                    self.sendEject(clientChannel, 122, 'Failed to locate your Account object.')
                    return

                avList = fields['ACCOUNT_AV_SET'][:6]
                avList += [0] * (6 - len(avList))

                # Prepare variables to store the avatar fields and the pending avatars.
                pendingAvatars = set()
                avatarFields = {}

                for avId in avList:
                    if avId:
                        # Add this avatar id to our pending avatars.
                        pendingAvatars.add(avId)

                        def handleAvRetrieve(dclass, fields, avId=avId):
                            if dclass != self.air.dclassesByName['DistributedToonUD']:
                                # This is not a valid avatar object.
                                self.sendEject(clientChannel, 122, 'An Avatar object in the account is invalid.')
                                return

                            # Throw in the avatar fields.
                            avatarFields[avId] = fields
                            pendingAvatars.remove(avId)
                            if not pendingAvatars:
                                handleAvRetrieveDone(avList, avatarFields)

                        # Query the avatar object.
                        self.air.dbInterface.queryObject(self.air.dbId, avId, handleAvRetrieve)

                if not pendingAvatars:
                    handleAvRetrieveDone(avList, avatarFields)
                    return

            # Query the Account object.
            self.air.dbInterface.queryObject(self.air.dbId, clientChannel >> 32, handleRetrieve)
        elif msgType == 6: # CLIENT_CREATE_AVATAR
            echoContext = dgi.getUint16()
            dnaString = dgi.getString()
            index = dgi.getUint8()

            dna = ToonDNA()
            result = dna.isValidNetString(dnaString)

            if not result:
                # Bad DNA string.
                self.sendEject(clientChannel, 122, 'Invalid Avatar DNA sent.')
                return

            if index > 6:
                # Bad index.
                self.sendEject(clientChannel, 122, 'Invalid Avatar index chosen.')
                return

            def handleAvatarResp(avId, fields):
                resp = PyDatagram()
                resp.addUint16(7) # CLIENT_CREATE_AVATAR_RESP
                resp.addUint16(echoContext)
                resp.addUint8(0)
                resp.addUint32(avId)

                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)

            def handleCreate(oldAvList, newAvList, avId):
                if not avId:
                    # The Avatar object could not be created.
                    self.sendEject(clientChannel, 122, 'Failed to create your Avatar object.')
                    return

                # Store the new Avatar index in the avatar set.
                newAvList[index] = avId

                # Store the Avatar in the Account's avatar set.
                self.air.dbInterface.updateObject(self.air.dbId,
                                                  clientChannel >> 32,
                                                  self.air.dclassesByName['AccountUD'],
                                                  {'ACCOUNT_AV_SET': newAvList},
                                                  {'ACCOUNT_AV_SET': oldAvList},
                                                  lambda fields: handleAvatarResp(avId, fields))

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['AccountUD']:
                    # The Account object could not be located.
                    self.sendEject(clientChannel, 122, 'Failed to locate your Account object.')
                    return

                oldAvList = fields['ACCOUNT_AV_SET']
                avList = oldAvList[:6]
                avList += [0] * (6 - len(avList))

                if avList[index]:
                    # This index isn't available.
                    self.sendEject(clientChannel, 122, 'The Avatar index chosen is not available.')
                    return

                # Get the default toon name.
                dna.makeFromNetString(dnaString)
                colorString = TTLocalizer.NumToColor[dna.headColor]
                animalType = TTLocalizer.AnimalToSpecies[dna.getAnimal()]
                name = colorString + ' ' + animalType

                # Pick a default shard.
                shardKeys = list(self.shardInfo.keys())
                if not shardKeys:
                    # There aren't available shards...
                    self.sendEject(clientChannel, 122, 'No Districts are available right now.')
                    return

                defaultShard = random.choice(shardKeys)

                # Put together the fields the avatar needs.
                # We don't need to put all of the DB
                # default values here as they are set in the DC file.
                toonFields = {'setName': (name,),
                              'WishNameState': ('OPEN',),
                              'WishName': ('',),
                              'setDNAString': (dnaString,),
                              'setFriendsList': ([],),
                              'setDefaultShard': (defaultShard,),}

                # Create the Toon object.
                self.air.dbInterface.createObject(self.air.dbId,
                                                  self.air.dclassesByName['DistributedToonUD'],
                                                  toonFields,
                                                  lambda avId: handleCreate(oldAvList, avList, avId))

            # Query the account.
            self.air.dbInterface.queryObject(self.air.dbId, clientChannel >> 32, handleRetrieve)
        elif msgType == 8: # CLIENT_GET_SHARD_LIST
            resp = PyDatagram()
            resp.addUint16(9) # CLIENT_GET_SHARD_LIST_RESP
            resp.addUint16(len(self.shardInfo))
            for shardId, shardInfo in self.shardInfo.iteritems():
                resp.addUint32(shardId)
                resp.addString(shardInfo[0]) # name
                resp.addUint32(shardInfo[1]) # pop

            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)
        elif msgType == 10: # CLIENT_GET_FRIEND_LIST
            pass
        elif msgType == 125: # CLIENT_LOGIN_TOONTOWN
            playToken = dgi.getString()
            serverVersion = dgi.getString()
            hashVal = dgi.getUint32()
            tokenType = dgi.getInt32()

            # Check the server version against the real one.
            ourVersion = config.GetString('server-version', '')
            if serverVersion != ourVersion:
                # Version mismatch.
                reason = 'Client version mismatch: client=%s, server=%s' % (serverVersion, ourVersion)
                self.sendEject(clientChannel, 122, reason)
                return

            # Check the DC hash against the expected one.
            # Unfortunately, the expected hash has to differ from
            # the hash that we use, since we need an Astronized
            # DC file. The expected hash should be the same one
            # that the original 2013 client uses.
            expectedHash = int(config.GetString('client-dc-hash', '0'))
            if hashVal != expectedHash:
                # DC hash mismatch.
                reason = 'Client DC hash mismatch: client=%s, server=%s' % (hashVal, expectedHash)
                self.sendEject(clientChannel, 122, reason)
                return

            # Check if this play token exists in the bridge.
            accountId = self.bridge.query(playToken)
            if accountId:

                def queryLoginResponse(dclass, fields):
                    if dclass != self.air.dclassesByName['AccountUD']:
                        # This isn't an Account object.
                        self.sendEject(clientChannel, 122, 'The Account object was unable to be queried.')
                        return

                    # Log in the account.
                    self.loginAccount(fields, clientChannel, accountId, playToken)

                # Query the Account object.
                self.air.dbInterface.queryObject(self.air.dbId, accountId, queryLoginResponse)
                return

            # Create a new Account object.
            account = {'ACCOUNT_AV_SET': [0] * 6,
                       'pirateAvatars': [0],
                       'HOUSE_ID_SET': [0] * 6,
                       'ESTATE_ID': 0,
                       'ACCOUNT_AV_SET_DEL': [],
                       'CREATED': time.ctime(),
                       'LAST_LOGIN': time.ctime()}

            def createLoginResponse(accountId):
                if not accountId:
                    self.sendEject(clientChannel, 122, 'The Account object was unable to be created.')
                    return

                # Put the account id in the account bridge.
                self.bridge.put(playToken, accountId)

                # Log in the account.
                self.loginAccount(account, clientChannel, accountId, playToken)

            # Create the Account in the database.
            self.air.dbInterface.createObject(self.air.dbId,
                                              self.air.dclassesByName['AccountUD'],
                                              account,
                                              createLoginResponse)
        elif msgType == 24: # CLIENT_OBJECT_UPDATE_FIELD
            # Certain fields need to be handled specially...
            # The only example of this right now is setChat.
            doId = dgi.getUint32()
            fieldNumber = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            #resp.addUint16(CLIENT_OBJECT_SET_FIELD)
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_OBJECT_SET_FIELD)
            resp.addUint32(doId)
            resp.addUint16(fieldNumber)
            resp.appendData(dcData)
            self.air.send(resp)

            '''
            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)
            '''
        elif msgType == 29: # CLIENT_SET_ZONE
            zoneId = dgi.getUint16()

            # Make sure we have an active shard.
            shardId = self.clientChannel2shardId.get(clientChannel)
            if not shardId:
                return

            # Prepare a context.
            if clientChannel not in self.clientChannel2context:
                self.clientChannel2context[clientChannel] = 0
            if clientChannel not in self.clientChannel2contextZone:
                self.clientChannel2contextZone[clientChannel] = {}

            context = self.clientChannel2context[clientChannel]

            # Save the zone according to the context.
            self.clientChannel2contextZone[clientChannel][context] = zoneId

            # Send a get state response back to the client.
            resp = PyDatagram()
            resp.addUint16(47) # CLIENT_GET_STATE_RESP
            resp.padBytes(12)
            resp.addUint16(zoneId)

            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)

            # This is the Toontown server equivalent of setting interest on a zone.
            # We'll transform it into a set interest request.

            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, 97)
            resp.addUint32(context)
            resp.addUint16(context)
            resp.addUint32(shardId)
            resp.addUint32(zoneId)
            self.air.send(resp)

            # Increment the context/handle.
            self.clientChannel2context[clientChannel] += 1
        elif msgType == 31: # CLIENT_SET_SHARD
            shardId = dgi.getUint32()
            if shardId not in self.shardInfo:
                # This is not a valid shard.
                self.sendEject(clientChannel, 122, 'Attempted to join an invalid District.')
                return

            # Increment the shard's population.
            self.shardInfo[shardId] = (self.shardInfo[shardId][0],
                                       self.shardInfo[shardId][1] + 1)

            # Keep track of the client's presence on this shard.
            self.clientChannel2shardId[clientChannel] = shardId

            resp = PyDatagram()
            resp.addUint16(47) # CLIENT_GET_STATE_RESP

            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)
        elif msgType == 32: # CLIENT_SET_AVATAR
            avId = dgi.getUint32()

            def handleAvatarRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonUD']:
                    # This is not an Avatar object.
                    self.sendEject(clientChannel, 122, 'An Avatar object was not retrieved.')
                    return

                target = clientChannel >> 32
                channel = self.air.GetAccountConnectionChannel(target)

                # First, give them a POSTREMOVE to unload the avatar, just in case they
                # disconnect while we're working.
                datagramCleanup = PyDatagram()
                datagramCleanup.addServerHeader(avId, channel, STATESERVER_OBJECT_DELETE_RAM)
                datagramCleanup.addUint32(avId)

                datagram = PyDatagram()
                datagram.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_ADD_POST_REMOVE)
                datagram.addBlob(datagramCleanup.getMessage())
                self.air.send(datagram)

                # Save the account ID.
                self.loadAvProgress.add(target)

                # Activate the avatar on the DBSS.
                self.air.sendActivate(avId, fields['setDefaultShard'][0], 1,
                    self.air.dclassesByName['DistributedToonUD'],
                    {'setCommonChatFlags': [0], 'setAccess': [OTPGlobals.AccessFull]})

                # Add the client to the avatar channel.
                dg = PyDatagram()
                dg.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_OPEN_CHANNEL)
                dg.addChannel(self.air.GetPuppetConnectionChannel(avId))
                self.air.send(dg)

                # Make the avatar the session object.
                self.air.clientAddSessionObject(channel, avId)

                # Set the client ID to associate the client channel with the avatar ID.
                dg = PyDatagram()
                dg.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_SET_CLIENT_ID)
                dg.addChannel(target << 32 | avId)
                self.air.send(dg)

                # Make the client own the avatar.
                self.air.setOwner(avId, channel)

            def handleAccountRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['AccountUD']:
                    # This is not an Account object.
                    self.sendEject(clientChannel, 122, 'An Account object was not retrieved.')
                    return

                # Get the avatar list.
                avList = fields['ACCOUNT_AV_SET'][:6]
                avList += [0] * (6 - len(avList))

                # Make sure the requested avatar is part of this account.
                if avId not in avList:
                    # Nope.
                    self.sendEject(clientChannel, 122, 'Attempted to play an Avatar not part of the Account.')
                    return

                # Fetch the avatar details.
                self.air.dbInterface.queryObject(self.air.dbId, avId, handleAvatarRetrieve)

            # Query the account.
            self.air.dbInterface.queryObject(self.air.dbId, clientChannel >> 32, handleAccountRetrieve)
        elif msgType == 37: # CLIENT_DISCONNECT
            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_DISCONNECT)
            self.air.send(resp)
        elif msgType == 52: # CLIENT_HEARTBEAT
            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_HEARTBEAT)
            self.air.send(resp)
        elif msgType == 67: # CLIENT_SET_NAME_PATTERN
            avId = dgi.getUint32()
            p1 = dgi.getInt16()
            f1 = dgi.getInt16()
            p2 = dgi.getInt16()
            f2 = dgi.getInt16()
            p3 = dgi.getInt16()
            f3 = dgi.getInt16()
            p4 = dgi.getInt16()
            f4 = dgi.getInt16()

            # Construct a pattern.
            pattern = [(p1, f1), (p2, f2),
                       (p3, f3), (p4, f4)]

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonUD']:
                    # This is not an Avatar object.
                    self.sendEject(clientChannel, 122, 'An Avatar object was not retrieved.')
                    return

                if fields['WishNameState'][0] != 'OPEN':
                    # This avatar is not nameable.
                    self.sendEject(clientChannel, 122, 'This Avatar is not nameable.')
                    return

                # Get the Toon name from the pattern.
                parts = []

                for p, f in pattern:
                    part = self.nameGenerator.nameDictionary.get(p, ('',''))[1]

                    if f:
                        part = part[:1].upper() + part[1:]
                    else:
                        part = part.lower()

                    parts.append(part)

                parts[2] += parts.pop(3) # Merge 2&3 (the last name) as there should be no space.

                while '' in parts:
                    parts.remove('')

                name = ' '.join(parts)

                # Update the Avatar object with the new name.
                self.air.dbInterface.updateObject(self.air.dbId, avId,
                                                  self.air.dclassesByName['DistributedToonUD'],
                                                  {'WishNameState': ('LOCKED',),
                                                   'WishName': ('',),
                                                   'setName': (name,)})

                # Prepare the pattern name response.
                resp = PyDatagram()
                resp.addUint16(68) # CLIENT_SET_NAME_PATTERN_ANSWER
                resp.addUint32(avId)
                resp.addUint8(0)

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)

            # Query the avatar.
            self.air.dbInterface.queryObject(self.air.dbId, avId, handleRetrieve)
        elif msgType == 70: # CLIENT_SET_WISHNAME
            avId = dgi.getUint32()
            name = dgi.getString()

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonUD']:
                    # This is not an Avatar object.
                    self.sendEject(clientChannel, 122, 'An Avatar object was not retrieved.')
                    return

                if fields['WishNameState'][0] != 'OPEN':
                    # This avatar is not nameable.
                    self.sendEject(clientChannel, 122, 'This Avatar is not nameable.')
                    return

                # Update the Avatar object with the new wish name.
                self.air.dbInterface.updateObject(self.air.dbId, avId,
                                                  self.air.dclassesByName['DistributedToonUD'],
                                                  {'WishNameState': ('PENDING',),
                                                   'WishName': (name,)})

                # Prepare the wish name response.
                resp = PyDatagram()
                resp.addUint16(71) # CLIENT_SET_WISHNAME_RESP
                resp.addUint32(avId)
                resp.addUint16(0)
                resp.addString(name)
                resp.addString('')
                resp.addString('')

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)

            # Query the avatar.
            self.air.dbInterface.queryObject(self.air.dbId, avId, handleRetrieve)
        elif msgType == 97: # CLIENT_ADD_INTEREST:
            try:
                interest = self.buildInterest(dgi)
            except:
                self.notify.warning('Malformed request for CLIENT_ADD_INTEREST!')
                return

            newZones = []

            for zone in interest.getZones():
                if not self.interestManager.has_interest_object_parent_and_zone(interest.getParent(), zone):
                    newZones.append(zone)
                else:
                    if len(interest.getZones()) == 1:
                        # This interest was already created and letting it go through empty would erase previous interest zones.
                        self.handleInterestDone(clientChannel, interest.getId(), interest.getContext())
                        return

            newVisZones = set()

            for newZoneId in newZones:
                newZoneInStreetBranch = self.getInStreetBranch(newZoneId)
                newZoneInCogHQ = self.getInCogHQ(newZoneId)

                if newZoneInStreetBranch:
                    newBranchZoneId = ZoneUtil.getBranchZone(newZoneId)

                    if newZoneId % 100 != 0:
                        newVisZones.update(self.getVisBranchZones(newZoneId))

                if newZoneInCogHQ:
                    newVisZones.update(self.getVisBranchZones(newZoneId))

            interest.setVisZones(newVisZones)

            killedZones = []
            oldVisZones = set()

            if self.interestManager.has_interest_object_id(interest.getId()):
                previousInterest = self.interestManager.get_interest_object_by_id(interest.getId())

                for zone in previousInterest.getZones():
                    if len(self.lookupInterest(previousInterest.getParent(), zone)) > 1:
                        continue

                    if interest.getParent() != previousInterest.getParent() or not interest.hasZone(zone):
                        killedZones.append(zone)

                oldInterestVisZones = previousInterest.getVisZones()

                interestVisZones = interest.getVisZones()

                for zoneId in oldInterestVisZones.difference(interestVisZones):
                    killedZones.append(zoneId)

                for zoneId in interestVisZones.difference(oldInterestVisZones):
                    if zoneId not in newZones and not self.interestManager.has_interest_object_parent_and_zone(interest.getParent(), zoneId):
                        newZones.append(zoneId)

                for k in killedZones:
                    if k in interest.getVisZones() or k in newZones:
                        killedZones.remove(k)

                '''
                resp = PyDatagram()
                resp.addUint16(CLIENT_OBJECT_DISABLE)

                for zone in killedZones:
                    resp.addUint32(zone)

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)
                '''

                self.closeZones(clientChannel, killedZones, interest.getParent())
                self.interestManager.remove_interest_object(self.interestManager.has_interest_object_id(interest.getId(), True))
            else:
                newZones.extend(list(interest.getVisZones()))

            finalZones = []

            for zone in newZones:
                if not self.interestManager.has_interest_object_parent_and_zone(interest.getParent(), zone, False, True):
                    finalZones.append(zone)

            print('{0}:{1}'.format(finalZones, interest.getVisZones()))
            self.interestManager.add_interest_object(interest)

            op = InterestOperation(self, 500, interest.getId(), interest.getContext(), interest.getParent(), finalZones, clientChannel)
            self.pendingInterests[interest.getContext()] = interest

            self.deferredCallback = DeferredCallback(self.handleInterestCompleteCallback, clientChannel, interest.getContext())

            resp = PyDatagram()
            resp.addServerHeader(clientChannel, interest.getParent(), CLIENT_ADD_INTEREST_MULTIPLE)

            resp.addUint32(interest.getContext())
            resp.addUint16(interest.getId())
            resp.addUint32(interest.getParent())
            resp.addUint16(len(finalZones))

            for zone in finalZones:
                print('Zone interest {0}'.format(zone))
                resp.addUint32(zone)

            self.air.send(resp)
        elif msgType == 99: # CLIENT_REMOVE_INTEREST
            try:
                interestId = dgi.getUint16()
            except:
                self.notify.warning('Malformed request for CLIENT_REMOVE_INTEREST!')
                return

            print('Interest ID: {0}'.format(interestId))

            oldVisZones = set()
            killZones = []

            if self.interestManager.has_interest_object_id(interestId):
                interest = self.interestManager.get_interest_object_by_id(interestId)

                for zone in interest.getZones():
                    if len(self.lookupInterest(interest.getParent(), zone)) == 1:
                        killZones.append(zone)

                        oldZoneId = zone
                        oldZoneInInterestBranch = self.getInStreetBranch(oldZoneId)
                        oldZoneInCogHQ = self.getInCogHQ(oldZoneId)

                        if oldZoneInInterestBranch:
                            oldBranchZoneId = ZoneUtil.getBranchZone(oldZoneId)

                            if oldZoneId % 100 != 0:
                                oldVisZones.update(self.getVisBranchZones(oldZoneId))

                            if oldZoneInCogHQ:
                                oldVisZones.update(self.getVisBranchZones(oldZoneId))

                                for zoneId in oldVisZones:
                                    killZones.append(zoneId)

                            del self.dnaStores[oldBranchZoneId]
                '''
                resp = PyDatagram()
                resp.addUint16(CLIENT_OBJECT_DISABLE)

                killZones = [4681, 401000001]

                for zone in killZones:
                    resp.addUint32(zone)

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)
                '''

                self.closeZones(clientChannel, killZones, interest.getParent())
                self.handleInterestDone(clientChannel, interest.getId(), interest.getContext())
                self.interestManager.remove_interest_object(interest)
            else:
                self.notify.info('Delete for unknown interest id {0}'.format(interestId))
        elif msgType == 102: # CLIENT_OBJECT_LOCATION
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()

            resp = PyDatagram()
            resp.addServerHeader(doId, clientChannel, STATESERVER_OBJECT_SET_LOCATION)

            resp.addUint32(parentId)
            resp.addUint32(zoneId)

            self.air.send(resp)
        elif msgType == 14: # CLIENT_GET_AVATAR_DETAILS
            pass
        elif msgType == 81: # CLIENT_GET_PET_DETAILS
            pass
        else:
            self.notify.warning('Received unknown message type %s from Client' % msgType)

    def handleResp(self, dgi):
        """
        This handles Astron message types that under normal conditions
        would go to the client. The packets are rearranged
        for the Disney client here.
        """

        clientChannel = dgi.getUint64()
        msgType = dgi.getUint16()
        resp = None

        print('Client: {0} requested msgType: {1}.'.format(clientChannel, msgType))

        if msgType == CLIENT_EJECT:
            resp = PyDatagram()
            resp.addUint16(4) # CLIENT_GO_GET_LOST
            resp.addUint16(dgi.getUint16())
            ret = dgi.getString()
            print(ret)
            resp.addString(ret)

            # Send it.
            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)
        elif msgType == CLIENT_DONE_INTEREST_RESP:
            contextId = dgi.getUint32()
            handle = dgi.getUint16()

            resp = PyDatagram()

            resp.addUint16(48)

            resp.addUint16(handle)
            resp.addUint32(contextId)

            # Send it.
            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)
        elif msgType == CLIENT_OBJECT_SET_FIELD:
            doId = dgi.getUint32()
            fieldId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            resp.addUint16(24) # CLIENT_OBJECT_UPDATE_FIELD
            resp.addUint32(doId)
            resp.addUint16(fieldId)
            resp.appendData(dcData)
        elif msgType == CLIENT_OBJECT_LOCATION:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()

            resp = PyDatagram()

            resp.addUint16(102) # CLIENT_OBJECT_LOCATION

            resp.addUint32(doId)
            resp.addUint32(parentId)
            resp.addUint32(zoneId)
        elif msgType == CLIENT_OBJECT_DISABLE:
            doId = dgi.getUint32()

            print('Client is deleting {0}'.format(doId))

            # if the object is in the list of owned objects, we do not want to
            # delete this object, as it was already generated elsewhere...
            if doId in self.ownedObjects:
                return

            # only delete the object if we've previously seen the objects
            # generate request sent by the StateServer...
            if not self.hasSeenObject(doId, True):
                return
            
            # double check to prevent sending this more than one time
            if doId in self.deletedObjectHistory:
                return

            self.deletedObjectHistory.append(doId)

            resp = PyDatagram()
            resp.addUint16(25) # CLIENT_OBJECT_DISABLE_RESP
            resp.addUint32(doId)
        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            classId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            # if the object is in the list of owned objects, we do not want to
            # generate this object, as it was already generated elsewhere...
            if doId in self.ownedObjects:
                return
            
            if self.hasSeenObject(doId):
                return

            if self.interestManager.hasInterestObjectZone(zoneId):
                resp = PyDatagram()
                resp.addUint16(34) # CLIENT_CREATE_OBJECT_REQUIRED
                resp.addUint32(parentId)
                resp.addUint32(zoneId)
                resp.addUint16(classId)
                resp.addUint32(doId)
                resp.appendData(dcData)

                if doId in self.deletedObjectHistory:
                    self.deletedObjectHistory.remove(doId)

                if not zoneId in self.seenObjects:
                    self.seenObjects[zoneId] = []
                if doId not in self.seenObjects[zoneId]:
                    self.seenObjects[zoneId].append(doId)

        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            classId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            if zoneId == 1:
                return

            resp = PyDatagram()
            resp.addUint16(35) # CLIENT_CREATE_OBJECT_REQUIRED_OTHER
            resp.addUint32(parentId)
            resp.addUint32(zoneId)
            resp.addUint16(classId)
            resp.addUint32(doId)
            resp.appendData(dcData)
        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER:
            if clientChannel >> 32 not in self.loadAvProgress:
                return

            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            classId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            resp.addUint16(15) # CLIENT_GET_AVATAR_DETAILS_RESP
            resp.addUint32(doId)
            resp.addUint8(0)
            resp.appendData(dcData)

            self.clientChannel2avId[clientChannel] = doId

            self.loadAvProgress.remove(clientChannel >> 32)

            self.ownedObjects.append(doId)
        else:
            self.notify.warning('Received unknown message type %s from Astron' % msgType)

        if not resp:
            return

        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)
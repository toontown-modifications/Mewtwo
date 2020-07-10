from direct.distributed.PyDatagram import *
from direct.distributed.MsgTypes import *
from direct.directnotify.DirectNotifyGlobal import directNotify
from game.toontown.makeatoon.NameGenerator import NameGenerator
from game.toontown.toon.ToonDNA import ToonDNA
from game.otp.distributed.OtpDoGlobals import *
from game.otp.otpbase import OTPGlobals
from game.otp.otpbase import OTPLocalizer
from game.toontown.toonbase import TTLocalizer
from game.toontown.hood import ZoneUtil
from game.toontown.toonbase import ToontownGlobals
from game.toontown.chat.TTWhiteList import TTWhiteList
from panda3d.toontown import DNAStorage, loadDNAFileAI
from game import genDNAFileName, extractGroupName
from game.toontown.friends.FriendsManagerUD import FriendsManagerUD
import json, time, os, random, requests

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

class ExtAgent:
    notify = directNotify.newCategory('ExtAgent')

    def __init__(self, air):
        self.air = air

        self.air.registerForChannel(5536)

        self.air.netMessenger.register(0, 'registerShard')
        self.air.netMessenger.register(1, 'magicWord')
        self.air.netMessenger.register(2, 'postAddFriend')

        self.air.netMessenger.accept('registerShard', self, self.registerShard)
        self.air.netMessenger.accept('postAddFriend', self, self.postAddFriend)

        self.shardInfo = {}

        self.nameGenerator = NameGenerator()
        self.bridge = JSONBridge()
        self.whiteList = TTWhiteList()

        self.loadAvProgress = set()

        self.clientChannel2avId = {}
        self.clientChannel2handle = {}
        self.dnaStores = {}
        self.chatOffenses = {}

        self.friendsManager = FriendsManagerUD(self)

        self.validZones = [ToontownGlobals.ToontownCentral,
                           ToontownGlobals.DonaldsDock,
                           ToontownGlobals.DaisyGardens,
                           ToontownGlobals.MinniesMelodyland,
                           ToontownGlobals.TheBrrrgh,
                           ToontownGlobals.DonaldsDreamland,
                           ToontownGlobals.SellbotHQ,
                           ToontownGlobals.CashbotHQ,
                           ToontownGlobals.LawbotHQ,
                           ToontownGlobals.WelcomeValleyBegin,
                           23000]
        self.blacklistZones = [ToontownGlobals.SellbotLobby, ToontownGlobals.LawbotOfficeExt, ToontownGlobals.LawbotLobby, ToontownGlobals.CashbotLobby, ToontownGlobals.WelcomeValleyEnd]

        self.wantServerDebug = config.GetBool('want-server-debugging', False)
        self.wantServerMaintenance = config.GetBool('want-server-maintenance', False)
        self.wantMembership = config.GetBool('want-membership', False)
        self.wantBlacklistWarnings = config.GetBool('want-blacklist-warnings', False)

        self.databasePath = 'otpd/databases/otpdb'

        if not os.path.exists(self.databasePath):
            os.makedirs(self.databasePath)

        self.sendAvailabilityToAPI()

    def getWhitelistedAccounts(self):
        with open('data/whitelistedAccounts.json') as data:
            accounts = json.load(data)
            return accounts

    def sendAvailabilityToAPI(self):
        if config.GetBool('want-localhost-api-testing', False):
            apiBase = '127.0.0.1'
        else:
            apiBase = 'otp-gs.rocketprogrammer.me'

        data = {
            'token': config.GetString('api-token', ''),
            'setter': self.wantServerMaintenance
        }

        try:
            req = requests.post('http://{0}:19135/api/setMaintenanceMode'.format(apiBase), json = data)
        except:
            self.notify.warning('Failed to send availability to API!')

    def postAddFriend(self, avId, friendId):
        self.friendsManager.postAddFriend(avId, friendId)

    def sendKick(self, avId, reason):
        clientChannel = self.air.GetPuppetConnectionChannel(avId)

        errorCode = 152
        message = OTPLocalizer.CRBootedReasons.get(errorCode)

        self.sendBoot(clientChannel, errorCode, message)
        self.sendEject(clientChannel, errorCode, message)

    def sendEject(self, clientChannel, errorCode, errorStr):
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_EJECT)
        dg.addUint16(errorCode)
        dg.addString(errorStr)
        self.air.send(dg)

    def sendBoot(self, clientChannel, errorCode, errorStr):
        # Prepare the eject response.
        resp = PyDatagram()
        resp.addUint16(4) # CLIENT_GO_GET_LOST
        resp.addUint16(errorCode)
        resp.addString(errorStr)

        # Send it.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)

    def sendSystemMessage(self, clientChannel, message):
        # Prepare the System Message response.
        resp = PyDatagram()
        resp.addUint16(78) # CLIENT_SYSTEM_MESSAGE
        resp.addString(message)

        # Send it.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)

    def registerShard(self, shardId, shardName):
        self.shardInfo[shardId] = (shardName, 0)

    def loginAccount(self, fields, clientChannel, accountId, playToken):
        # If somebody is logged into this account, disconnect them.
        errorCode = 100
        self.sendEject(self.air.GetAccountConnectionChannel(accountId), errorCode, OTPLocalizer.CRBootedReasons.get(errorCode))

        # Wait half a second before continuing to avoid a race condition.
        taskMgr.doMethodLater(0.5,
                              lambda x: self.finishLoginAccount(fields, clientChannel, accountId, playToken),
                              self.air.uniqueName('wait-acc-%s' % accountId), appendTask=False)

    def finishLoginAccount(self, fields, clientChannel, accountId, playToken):
        # If there's anybody on the account, kill them for redundant login:
        errorCode = 100

        datagram = PyDatagram()
        datagram.addServerHeader(self.air.GetAccountConnectionChannel(accountId), self.air.ourChannel, CLIENTAGENT_EJECT)
        datagram.addUint16(errorCode)
        datagram.addString(OTPLocalizer.CRBootedReasons.get(errorCode))
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

        if self.wantMembership:
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
        if zoneId in self.blacklistZones:
            return []
        branchZoneId = ZoneUtil.getBranchZone(zoneId)
        hoodId = ZoneUtil.getHoodId(branchZoneId)
        dnaStore = self.dnaStores.get(branchZoneId)

        if hoodId not in self.validZones:
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

    def getAvatars(self, clientChannel):
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

    def filterWhiteList(self, message):
        modifications = []
        words = message.split(' ')
        offset = 0

        for word in words:
            if word and not self.whiteList.isWord(word):
                modifications.append((offset, offset + len(word) - 1))

            offset += len(word) + 1

        cleanMesssage = message

        for modStart, modStop in modifications:
            cleanMesssage = cleanMesssage[:modStart] + '*' * (modStop - modStart + 1) + cleanMesssage[modStop + 1:]

        return cleanMesssage, modifications

    def handleDatagram(self, dgi):
        """
        This handles datagrams coming directly from the Toontown 2013 client.
        These datagrams may be reformatted in a way that can appease Astron,
        or are totally game-specific and will have their own handling.
        """

        clientChannel = dgi.getUint64()
        msgType = dgi.getUint16()

        if self.wantServerDebug:
            print('handleDatagram: {0}:{1}'.format(clientChannel, msgType))

        if msgType == 3: # CLIENT_GET_AVATARS
            self.getAvatars(clientChannel)
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

                target = clientChannel >> 32

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
                              'setDISLid': (target,),
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
            avId = self.air.getAvatarIdFromSender()

            self.friendsManager.getFriendsListRequest(avId)
        elif msgType == 125: # CLIENT_LOGIN_TOONTOWN
            try:
                playToken = dgi.getString()
                serverVersion = dgi.getString()
                hashVal = dgi.getUint32()
                tokenType = dgi.getInt32()
                wantMagicWords = dgi.getString()
            except:
                message = 'You have been ejected for attempting to send a incorrectly formatted datagram.'
                self.sendBootMessage(clientChannel, 122, message)
                self.sendEject(clientChannel, 122, message)

            if playToken in ['Rocket', 'developer']:
                # We got ourselves a skid!
                errorCode = 288
                message = 'Sorry, you have used up all of your available minutes this month.'

                self.sendBoot(clientChannel, errorCode, message)
                self.sendEject(clientChannel, errorCode, message)
                return

            print('{0} is trying to login!'.format(playToken))

            def callback(remoteIp, remotePort, localIp, localPort):
                print(remoteIp)

            self.air.getNetworkAddress(self.air.getMsgSender(), callback)

            if self.wantServerMaintenance and playToken not in self.getWhitelistedAccounts():
                errorCode = 151
                message = 'You have been logged out by an administrator working on the servers.'

                self.sendBoot(clientChannel, errorCode, message)
                self.sendEject(clientChannel, errorCode, message)
                return

            # Check the server version against the real one.
            ourVersion = config.GetString('server-version', '')
            if serverVersion != ourVersion:
                # Version mismatch.
                reason = 'Client version mismatch: client=%s, server=%s' % (serverVersion, ourVersion)
                self.sendEject(clientChannel, 122, reason)
                return

            # Check the client DC hash against the server's DC hash.
            if hashVal != self.air.hashVal:
                # DC hash mismatch.
                reason = 'Client DC hash mismatch: client=%s, server=%s' % (hashVal, self.air.hashVal)
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
            # Certain fields need to be handled specifically...
            # The only example of this right now is setTalk.
            doId = dgi.getUint32()
            fieldNumber = dgi.getUint16()
            dcData = dgi.getRemainingBytes()
            avClientChannel = self.air.GetPuppetConnectionChannel(doId)

            if fieldNumber == 103: # setTalk field
                # We'll have to unpack the data and send our own datagrams.
                toon = self.air.dclassesByName['DistributedToonUD']
                talkField = toon.getFieldByName('setTalk')
                unpacker = DCPacker()
                unpacker.setUnpackData(dcData)
                unpacker.beginUnpack(talkField)
                fieldArgs = talkField.unpackArgs(unpacker)
                unpacker.endUnpack()

                if len(fieldArgs) != 6:
                    # Bad field data.
                    return

                message = fieldArgs[3]

                if not message:
                    return

                if message[0] == '~':
                    # Route this to the Magic Word manager.
                    self.air.netMessenger.send('magicWord', [message, doId])
                    return

                cleanMessage, modifications = self.filterWhiteList(message)

                # TODO: Fix this
                if self.wantBlacklistWarnings:
                    for word in words:
                        if word.lower() in TTLocalizer.Blacklist:
                            if not doId in self.chatOffenses:
                                self.chatOffenses[doId] = 0

                        self.chatOffenses[doId] += 1

                        if self.chatOffenses[doId] == 1:
                            message = 'Warning - Watch your language. \nUsing inappropriate words will get you suspended. You said "{0}"'.format(message)
                            self.sendSystemMessage(avClientChannel, message)
                        elif self.chatOffenses[doId] == 2:
                            message = 'Final Warning. If you continue using inappropriate language you will be suspended. You said "{0}"'.format(message)
                            self.sendSystemMessage(avClientChannel, message)
                        elif self.chatOffenses[doId] == 3:
                            message = 'Your account has been suspended for 24 hours for using inappropriate language. You said "{0}"'.format(message)
                            self.sendSystemMessage(avClientChannel, message)
                            self.sendKick(doId, 'Language')
                            del self.chatOffenses[doId]

                # Construct a new aiFormatUpdate.
                resp = toon.aiFormatUpdate('setTalk', doId, doId,
                                           self.air.ourChannel,
                                           [0, 0, '', cleanMessage, modifications, 0])
                self.air.send(resp)
                return
            elif fieldNumber == 104: # setTalkWhisper field
                # We'll have to unpack the data and send our own datagrams.
                toon = self.air.dclassesByName['DistributedToonUD']
                talkWhisperField = toon.getFieldByName('setTalkWhisper')
                unpacker = DCPacker()
                unpacker.setUnpackData(dcData)
                unpacker.beginUnpack(talkWhisperField)
                fieldArgs = talkWhisperField.unpackArgs(unpacker)
                unpacker.endUnpack()

                accId = self.air.getAccountIdFromSender()

                if not accId:
                    return

                avId = self.air.getAvatarIdFromSender()

                if not avId:
                    self.air.writeServerEvent('suspicious', accId = accId, issue = 'Account sent chat without an avatar!', message = message)
                    return

                if len(fieldArgs) != 6:
                    # Bad field data.
                    return

                message = fieldArgs[3]

                if not message:
                    return

                def handleAvatar(dclass, fields):
                    if dclass != self.air.dclassesByName['DistributedToonUD']:
                        return

                    senderName = fields['setName'][0]
                    senderFriendsList = fields['setFriendsList'][0]

                    if (doId, 1) in senderFriendsList:
                        cleanMessage, modifications = message, []
                    else:
                        cleanMessage, modifications = self.filterWhiteList(message)

                    # Construct a new aiFormatUpdate.
                    resp = toon.aiFormatUpdate('setTalkWhisper', doId, doId, self.air.ourChannel, [avId, accId, senderName, cleanMessage, modifications, 0])
                    self.air.send(resp)

                self.air.dbInterface.queryObject(self.air.dbId, avId, handleAvatar)

            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_OBJECT_SET_FIELD)
            resp.addUint32(doId)
            resp.addUint16(fieldNumber)
            resp.appendData(dcData)
            self.air.send(resp)
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

            if avId == 0:
                # We assume the avatar has logged out to the Pick A Toon.
                # Lets unload.

                # Grab the legitimate avId.
                currentAvId = self.air.getAvatarIdFromSender()

                # Tell everybody were going offline.
                self.friendsManager.goingOffline(currentAvId)

                target = clientChannel >> 32
                channel = self.air.GetAccountConnectionChannel(target)

                # Remove our POST_REMOVES.
                dg = PyDatagram()
                dg.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_CLEAR_POST_REMOVES)
                self.air.send(dg)

                # Remove avatar channel:
                dg = PyDatagram()
                dg.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_CLOSE_CHANNEL)
                dg.addChannel(self.air.GetPuppetConnectionChannel(currentAvId))
                self.air.send(dg)

                # Reset the session object.
                dg = PyDatagram()
                dg.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_REMOVE_SESSION_OBJECT)
                dg.addUint32(currentAvId)
                self.air.send(dg)

                # Unload avatar object:
                dg = PyDatagram()
                dg.addServerHeader(currentAvId, channel, STATESERVER_OBJECT_DELETE_RAM)
                dg.addUint32(currentAvId)
                self.air.send(dg)
                return

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

                if self.wantMembership:
                    access = OTPGlobals.AccessFull
                else:
                    access = OTPGlobals.AccessVelvetRope

                activateFields = {
                    'setCommonChatFlags': [0],
                    'setAccess': [access]
                }

                # Activate the avatar on the DBSS.
                self.air.sendActivate(avId, fields['setDefaultShard'][0], 1,
                    self.air.dclassesByName['DistributedToonUD'], activateFields)

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

                # Tell the friends manager that an avatar is coming online.
                for x, y in fields['setFriendsList'][0]:
                    self.friendsManager.comingOnline(avId, x)

                # Tell the Party manager as well.
                self.air.partyManager.avatarOnline(avId)

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
            avId = self.air.getAvatarIdFromSender()

            if avId:
                # If we have a avId, tell everybody were going offline.
                self.friendsManager.goingOffline(avId)

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

            # If we have a avId, update the Avatar object with the new wish name.
            fields = {
                'WishNameState': ('APPROVED',),
                'WishName': (name,),
                'setName': (name,),
                }

            if avId:
                self.air.dbInterface.updateObject(self.air.dbId, avId, self.air.dclassesByName['DistributedToonUD'], fields)

            # Prepare the wish name response.
            resp = PyDatagram()
            resp.addUint16(71) # CLIENT_SET_WISHNAME_RESP
            resp.addUint32(avId)
            resp.addUint16(0)
            resp.addString('')
            resp.addString(name)
            resp.addString('')

            # Send it.
            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addString(resp.getMessage())
            self.air.send(dg)

        elif msgType == 97: # CLIENT_ADD_INTEREST
            # Reformat the packets for the CA.
            handle = dgi.getUint16()
            context = dgi.getUint32()
            parentId = dgi.getUint32()
            zones = []

            while dgi.getRemainingSize() != 0:
                zones.append(dgi.getUint32())

            if len(zones) == 1:
                zoneId = zones[0]

                visZones = set()

                isStreetBranch = self.getInStreetBranch(zoneId)
                isCogHQ = self.getInCogHQ(zoneId)
                isPlayground = ZoneUtil.isPlayground(zoneId)
                branchId = ZoneUtil.getBranchZone(zoneId)
                isWelcomeValley = ZoneUtil.isWelcomeValley(zoneId)

                if isStreetBranch:
                    zoneId = ZoneUtil.getCanonicalZoneId(zoneId)
                    branchId = ZoneUtil.getBranchZone(zoneId)

                    if zoneId % 100 != 0:
                        visZones.update(self.getVisBranchZones(zoneId))

                if isCogHQ:
                    visZones.update(self.getVisBranchZones(zoneId))

                # Set interest on the VisZones.
                for zone in visZones:
                    zones.append(zone)

                loaderName = ZoneUtil.getLoaderName(zoneId)

                if branchId and isPlayground and loaderName != 'safeZoneLoader':
                    # Set object location.
                    dg = PyDatagram()
                    dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_OBJECT_LOCATION)
                    dg.addUint32(self.clientChannel2avId[clientChannel])
                    dg.addUint32(parentId)
                    dg.addUint32(zoneId)
                    self.air.send(dg)

                    # Set interest on the branch ID.
                    zones.append(branchId)

                    if clientChannel in self.clientChannel2handle:
                        # Use the same handle to alter the interest.
                        handle = self.clientChannel2handle[clientChannel]
                    else:
                        # Save the handle for later.
                        self.clientChannel2handle[clientChannel] = handle

            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_ADD_INTEREST_MULTIPLE)
            resp.addUint32(context)
            resp.addUint16(handle)
            resp.addUint32(parentId)
            resp.addUint16(len(zones))
            for zone in zones:
                resp.addUint32(zone)
            self.air.send(resp)
        elif msgType == 99: # CLIENT_REMOVE_INTEREST
            handle = dgi.getUint16()
            context = 0

            if dgi.getRemainingSize() > 0:
                context = dgi.getUint32()

            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_REMOVE_INTEREST)
            resp.addUint32(context)
            resp.addUint16(handle)
            self.air.send(resp)
        elif msgType == 102: # CLIENT_OBJECT_LOCATION
            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_OBJECT_LOCATION)
            resp.addUint32(dgi.getUint32())
            resp.addUint32(dgi.getUint32())
            resp.addUint32(dgi.getUint32())
            self.air.send(resp)
        elif msgType == 14: # CLIENT_GET_AVATAR_DETAILS
            avatarId = dgi.getUint32()

            def handleAvatar(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonUD']:
                    return

                requiredPacker = DCPacker()
                otherCount = 0
                otherPacker = DCPacker()

                for f in range(dclass.getNumInheritedFields()):
                    field = dclass.getInheritedField(f)

                    if field.isRequired():
                        requiredPacker.beginPack(field)
                        if field.getName() in fields:
                            field.packArgs(requiredPacker, fields[field.getName()])
                        else:
                            requiredPacker.packDefaultValue()

                        requiredPacker.endPack()

                    elif field.isRam() and field.getName() in fields:
                        otherPacker.rawPackUint16(field.getNumber())
                        otherPacker.beginPack(field)
                        field.packArgs(otherPacker, fields[field.getName()])
                        otherPacker.endPack()
                        otherCount += 1

                # Our avatar details response.
                resp = PyDatagram()

                resp.addUint16(15) # CLIENT_GET_AVATAR_DETAILS_RESP

                resp.addUint32(avatarId)
                resp.addUint8(0)
                resp.appendData(requiredPacker.getString())
                resp.appendData(otherPacker.getString())

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)

            self.air.dbInterface.queryObject(self.air.dbId, avatarId, handleAvatar)
        elif msgType == 81: # CLIENT_GET_PET_DETAILS
            petId = dgi.getUint32()

            def handlePet(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedPetAI']:
                    return

                requiredPacker = DCPacker()
                otherCount = 0
                otherPacker = DCPacker()

                for f in range(dclass.getNumInheritedFields()):
                    field = dclass.getInheritedField(f)

                    if field.isRequired():
                        requiredPacker.beginPack(field)
                        if field.getName() in fields:
                            field.packArgs(requiredPacker, fields[field.getName()])
                        else:
                            requiredPacker.packDefaultValue()

                        requiredPacker.endPack()

                    elif field.isRam() and field.getName() in fields:
                        otherPacker.rawPackUint16(field.getNumber())
                        otherPacker.beginPack(field)
                        field.packArgs(otherPacker, fields[field.getName()])
                        otherPacker.endPack()
                        otherCount += 1

                # Our pet details response.
                resp = PyDatagram()

                resp.addUint16(82) # CLIENT_GET_PET_DETAILS_RESP

                resp.addUint32(petId)
                resp.addUint8(0)
                resp.appendData(requiredPacker.getString())
                resp.appendData(otherPacker.getString())

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addString(resp.getMessage())
                self.air.send(dg)

            self.air.dbInterface.queryObject(self.air.dbId, petId, handlePet)
        elif msgType == 56: # CLIENT_REMOVE_FRIEND
            avId = self.air.getAvatarIdFromSender()

            friendId = dgi.getUint32()

            self.friendsManager.removeFriend(avId, friendId)
        elif msgType == 49: # CLIENT_DELETE_AVATAR
            avId = dgi.getUint32()
            target = clientChannel >> 32

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['AccountUD']:
                    # The Account object could not be located.
                    self.sendEject(clientChannel, 122, 'Failed to locate your Account object.')
                    return

                avList = fields['ACCOUNT_AV_SET'][:6]
                avList += [0] * (6 - len(avList))

                # Make sure the requested avatar is part of this account.
                if avId not in avList:
                    # Nope.
                    self.sendEject(clientChannel, 122, 'Attempted to delete an Avatar not part of the Account.')
                    return

                # Get the index of this avatar.
                index = avList.index(avId)
                avList[index] = 0

                # We will now add this avatar to ACCOUNT_AV_SET_DEL.
                avatarsRemoved = list(fields.get('ACCOUNT_AV_SET_DEL', []))
                avatarsRemoved.append([avId, int(time.time())])

                # Get the estate ID of this account.
                estateId = fields.get('ESTATE_ID', 0)

                if estateId != 0:
                    # The following will assume that the house already exists,
                    # however it shouldn't be a problem if it doesn't.

                    estateFields = {
                        'setSlot{0}ToonId'.format(index): [0],
                        'setSlot{0}Items'.format(index): [[]]
                        }

                    self.air.dbInterface.updateObject(self.air.dbId, estateId, self.air.dclassesByName['DistributedEstateAI'], estateFields)

                self.friendsManager.clearList(avId)

                newFields = {
                    'ACCOUNT_AV_SET': avList,
                    'ACCOUNT_AV_SET_DEL': avatarsRemoved
                }

                oldFields = {
                    'ACCOUNT_AV_SET': fields['ACCOUNT_AV_SET'],
                    'ACCOUNT_AV_SET_DEL': fields['ACCOUNT_AV_SET_DEL']
                    }

                def handleRemove(fields):
                    if fields:
                        # The avatar was unable to be removed from the account! Kill the account.
                        self.sendEject(clientChannel, 122, 'Database failed to mark the avatar as removed!')
                        return

                # We can now update the account with the new data. __handleRemove is the
                # callback which will be called upon completion of updateObject.
                self.air.dbInterface.updateObject(self.air.dbId, target, self.air.dclassesByName['AccountUD'], newFields, oldFields, handleRemove)

                self.getAvatars(clientChannel)

            self.air.dbInterface.queryObject(self.air.dbId, target, handleRetrieve)
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

        if self.wantServerDebug:
            print('Client: {0} requested msgType: {1}.'.format(clientChannel, msgType))

        if msgType == CLIENT_EJECT:
            resp = PyDatagram()
            resp.addUint16(4) # CLIENT_GO_GET_LOST
            resp.addUint16(dgi.getUint16())
            resp.addString(dgi.getString())
        elif msgType == CLIENT_DONE_INTEREST_RESP:
            contextId = dgi.getUint32()
            handle = dgi.getUint16()

            resp = PyDatagram()
            resp.addUint16(48) # CLIENT_DONE_INTEREST_RESP
            resp.addUint16(handle)
            resp.addUint32(contextId)
        elif msgType == CLIENT_ADD_INTEREST:
            pass
        elif msgType == CLIENT_OBJECT_SET_FIELD:
            doId = dgi.getUint32()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            resp.addUint16(24) # CLIENT_OBJECT_UPDATE_FIELD
            resp.addUint32(doId)
            resp.appendData(dcData)
        elif msgType == CLIENT_OBJECT_LOCATION:
            resp = PyDatagram()
            resp.addUint16(102) # CLIENT_OBJECT_LOCATION
            resp.addUint32(dgi.getUint32())
            resp.addUint32(dgi.getUint32())
            resp.addUint32(dgi.getUint32())
        elif msgType == CLIENT_OBJECT_DISABLE:
            resp = PyDatagram()
            resp.addUint16(25) # CLIENT_OBJECT_DISABLE
            resp.appendData(dgi.getRemainingBytes())
        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            classId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            resp.addUint16(34) # CLIENT_CREATE_OBJECT_REQUIRED
            resp.addUint32(parentId)
            resp.addUint32(zoneId)
            resp.addUint16(classId)
            resp.addUint32(doId)
            resp.appendData(dcData)
        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            classId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

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
        elif msgType == CLIENT_OBJECT_DISABLE_OWNER:
            doId = dgi.getUint32()

            resp = PyDatagram()
            resp.addUint16(CLIENT_OBJECT_DISABLE_OWNER)
            resp.addUint32(doId)
        else:
            self.notify.warning('Received unknown message type %s from Astron' % msgType)

        if not resp:
            return

        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)
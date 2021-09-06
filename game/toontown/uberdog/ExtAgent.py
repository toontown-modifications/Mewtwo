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
from game.toontown.uberdog.ServerBase import ServerBase
from game.toontown.discord.Webhook import Webhook
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from datetime import datetime
import json, time, os, random, requests, binascii, base64, limeade

class ServerGlobals:
    FINAL_TOONTOWN = 1
    TEST_TOONTOWN_2012 = 2
    TOONTOWN_JP_2010 = 3

    serverToName = {
        FINAL_TOONTOWN: 'Final Toontown',
        TEST_TOONTOWN_2012: 'Test Toontown 2012',
        TOONTOWN_JP_2010: 'Toontown Japan 2010'
    }

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
            json.dump(self.__bridge, f, sort_keys = 1, indent = 4, separators = [',', ': '])

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

class ExtAgent(ServerBase):
    notify = directNotify.newCategory('ExtAgent')

    def __init__(self, air):
        ServerBase.__init__(self)

        self.air = air

        self.air.registerForChannel(5536)

        self.air.netMessenger.register(0, 'registerShard')
        self.air.netMessenger.register(1, 'magicWord')
        self.air.netMessenger.register(2, 'postAddFriend')
        self.air.netMessenger.register(5, 'magicWordApproved')
        self.air.netMessenger.register(6, 'refreshModules')
        self.air.netMessenger.register(7, 'banPlayer')

        self.air.netMessenger.accept('registerShard', self, self.registerShard)
        self.air.netMessenger.accept('postAddFriend', self, self.postAddFriend)
        self.air.netMessenger.accept('refreshModules', self, self.refreshModules)
        self.air.netMessenger.accept('banPlayer', self, self.banPlayer)

        self.shardInfo = {}

        self.nameGenerator = NameGenerator()
        self.bridge = JSONBridge()
        self.whiteList = TTWhiteList()

        self.loadAvProgress = set()

        self.clientChannel2avId = {}
        self.clientChannel2handle = {}
        self.dnaStores = {}
        self.zoneVisDict = {}
        self.chatOffenses = {}
        self.accId2playToken = {}
        self.memberInfo = {}
        self.staffMembers = {}

        self.friendsManager = FriendsManagerUD(self)

        self.validVisZones = [ToontownGlobals.SillyStreet,
                              ToontownGlobals.LoopyLane,
                              ToontownGlobals.PunchlinePlace,
                              ToontownGlobals.BarnacleBoulevard,
                              ToontownGlobals.SeaweedStreet,
                              ToontownGlobals.LighthouseLane,
                              ToontownGlobals.ElmStreet,
                              ToontownGlobals.MapleStreet,
                              ToontownGlobals.OakStreet,
                              ToontownGlobals.AltoAvenue,
                              ToontownGlobals.BaritoneBoulevard,
                              ToontownGlobals.TenorTerrace,
                              ToontownGlobals.WalrusWay,
                              ToontownGlobals.SleetStreet,
                              ToontownGlobals.PolarPlace,
                              ToontownGlobals.LullabyLane,
                              ToontownGlobals.PajamaPlace,
                              ToontownGlobals.SellbotHQ,
                              ToontownGlobals.SellbotFactoryExt,
                              ToontownGlobals.CashbotHQ,
                              ToontownGlobals.LawbotHQ]

        self.blacklistZones = [
            ToontownGlobals.SellbotLobby,
            ToontownGlobals.LawbotOfficeExt,
            ToontownGlobals.LawbotLobby,
            ToontownGlobals.CashbotLobby]

        self.wantMembership = config.GetBool('want-membership', False)

        self.databasePath = 'otpd/databases/otpdb'

        if not os.path.exists(self.databasePath):
            # Create our database folder.
            os.makedirs(self.databasePath)

        self.banEndpointBase = 'https://toontastic.sunrise.games/bans/{0}'

        self.requestHeaders = {
            'User-Agent': 'Sunrise Games - ExtAgent'
        }

        # If you truly need these, ask Rocket.
        self.rpcKey = config.GetString('rpc-key')
        self.playTokenDecryptKey = config.GetString('token-key')

        self.wantTokenExpirations = config.GetBool('want-token-expirations', False)

        # Enable information logging.
        self.notify.setInfo(True)

        # Load our DNA files...
        # Vis Zones shouldn't be loaded per interest, but rather on UD startup.
        self.loadVisZones()

    def refreshModules(self):
        limeade.refresh()

    def banPlayer(self, avatarId, message, reason):
        def handleRetrieve(dclass, fields):
            if dclass != self.air.dclassesByName['DistributedToonUD']:
                return

            accountId = fields['setDISLid'][0]
            playToken = self.air.extAgent.accId2playToken.get(accountId, '')

            self.air.extAgent.sendKick(avatarId, message)
            self.air.extAgent.banAccount(playToken, message, reason, True)

        # Query the avatar to get some account information.
        self.air.dbInterface.queryObject(self.air.dbId, avatarId, handleRetrieve)

    def getStatus(self):
        try:
            serverType = ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN]
            endpoint = 'http://unite.sunrise.games:19135/api/getStatusForServer?serverType={0}'
            request = requests.get(endpoint.format(serverType), headers = self.requestHeaders)
            return request.text
        except:
            self.notify.warning('Failed to get status!')
            return False

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
        dg.addBlob(resp.getMessage())
        self.air.send(dg)

    def sendSystemMessage(self, clientChannel, message, aknowledge = False):
        # Prepare the System Message response.
        resp = PyDatagram()

        if aknowledge:
            resp.addUint16(123) # CLIENT_SYSTEMMESSAGE_AKNOWLEDGE
        else:
            resp.addUint16(78) # CLIENT_SYSTEM_MESSAGE

        resp.addString(message)

        # Send it.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addBlob(resp.getMessage())
        self.air.send(dg)

    def banAccount(self, playToken, message, banReason = 'Chat Filter', silent = False):
        endpoint = self.banEndpointBase.format('BanAccount.php')
        emailDispatchEndpoint = self.banEndpointBase.format('ChatBanEmail.php')

        banData = {
            'username': playToken,
            'banReason': banReason,
            'secretKey': self.rpcKey
        }

        emailData = {
            'playToken': playToken,
            'chatMessages': message,
            'secretKey': self.rpcKey
        }

        banRequest = requests.post(endpoint, banData, headers = self.requestHeaders)

        if not silent:
            emailRequest = requests.post(emailDispatchEndpoint, emailData, headers = self.requestHeaders)

    def approveName(self, avId):
        toonDC = simbase.air.dclassesByName['DistributedToonUD']

        fields = {
            'WishNameState': ('APPROVED',)
        }

        simbase.air.dbInterface.updateObject(simbase.air.dbId, avId, toonDC, fields)

    def rejectName(self, avId):
        toonDC = simbase.air.dclassesByName['DistributedToonUD']

        fields = {
            'WishNameState': ('REJECTED',)
        }

        simbase.air.dbInterface.updateObject(simbase.air.dbId, avId, toonDC, fields)

    def warnPlayer(self, clientChannel, reason):
        self.sendSystemMessage(clientChannel, reason, True)

    def registerShard(self, shardId, shardName):
        self.shardInfo[shardId] = (shardName, 0)

    def loginAccount(self, fields, clientChannel, accountId, playToken, openChat, isPaid, dislId, linkedToParent):
        # If somebody is logged into this account, disconnect them.
        errorCode = 100
        self.sendEject(self.air.GetAccountConnectionChannel(accountId), errorCode, OTPLocalizer.CRBootedReasons.get(errorCode))

        # Wait half a second before continuing to avoid a race condition.
        taskMgr.doMethodLater(0.5,
                              lambda x: self.finishLoginAccount(fields, clientChannel, accountId, playToken, openChat, isPaid, dislId, linkedToParent),
                              self.air.uniqueName('wait-acc-%s' % accountId), appendTask=False)

    def getCreationDate(self, fields):
        # Grab the account creation date from our fields.
        creationDate = fields.get('CREATED', '')

        try:
            creationDate = datetime.fromtimestamp(time.mktime(time.strptime(creationDate)))
        except ValueError:
            creationDate = ''

        return creationDate

    def getAccountDays(self, fields):
        # Retrieve the creation date.
        creationDate = self.getCreationDate(fields)

        accountDays = -1

        if creationDate:
            now = datetime.fromtimestamp(time.mktime(time.strptime(time.ctime())))
            accountDays = abs((now - creationDate).days)

        return accountDays

    def finishLoginAccount(self, fields, clientChannel, accountId, playToken, openChat, isPaid, dislId, linkedToParent):
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
        resp.addUint8(0) # returnCode
        resp.addString('All Ok') # respString
        resp.addUint32(dislId) # accountNumber
        resp.addString(playToken) # accountName
        resp.addUint8(1) # accountNameApproved
        resp.addString('YES') # openChatEnabled
        resp.addString('YES') # createFriendsWithChat
        resp.addString('YES') # chatCodeCreationRule
        resp.addUint32(int(time.time())) # sec
        resp.addUint32(int(time.process_time())) # usec

        if self.isProdServer():
            if isPaid:
                resp.addString('FULL') # access
                self.memberInfo[accountId] = playToken
            else:
                resp.addString('unpaid')

            if openChat:
                resp.addString('YES') # WhiteListResponse
            else:
                resp.addString('NO') # WhiteListResponse
        else:
            if self.wantMembership:
                resp.addString('FULL') # access
            else:
                resp.addString('unpaid') # access

            resp.addString('YES') # WhiteListResponse

        resp.addString(time.strftime('%Y-%m-%d %H:%M:%S')) # lastLoggedInStr
        resp.addInt32(self.getAccountDays(fields)) # accountDays
        resp.addString('WITH_PARENT_ACCOUNT' if linkedToParent else 'NO_PARENT_ACCOUNT') # toonAccountType
        resp.addString(playToken) # userName

        # Dispatch the response to the client.
        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addBlob(resp.getMessage())
        self.air.send(dg)

        self.accId2playToken[accountId] = playToken

    def getInStreetBranch(self, zoneId):
        if not ZoneUtil.isPlayground(zoneId):
            where = ZoneUtil.getWhereName(zoneId, True)
            return where == 'street'

        return False

    def getInCogHQ(self, zoneId):
        if ZoneUtil.isCogHQZone(zoneId):
            return True

        return False

    def loadVisZones(self):
        self.notify.info('Loading DNA files...')
        for zoneId in self.validVisZones:
            self.loadVisZone(zoneId)

    def loadVisZone(self, zoneId):
        branchZoneId = ZoneUtil.getBranchZone(zoneId)
        hoodId = ZoneUtil.getHoodId(branchZoneId)

        dnaStore = DNAStorage() # TODO: do I even need this?
        dnaFileName = genDNAFileName(branchZoneId)
        loadDNAFileAI(dnaStore, dnaFileName)
        self.dnaStores[branchZoneId] = dnaStore

        for i in range(dnaStore.getNumDNAVisGroupsAI()):
            visGroup = dnaStore.getDNAVisGroupAI(i)
            groupFullName = visGroup.getName()
            visZoneId = int(extractGroupName(groupFullName))
            visZoneId = ZoneUtil.getTrueZoneId(visZoneId, zoneId)
            visibles = []

            for i in range(visGroup.getNumVisibles()):
                visibles.append(int(visGroup.getVisibleName(i)))

            visibles.append(ZoneUtil.getBranchZone(visZoneId))
            self.zoneVisDict[visZoneId] = visibles

    def getVisBranchZones(self, zoneId):
        if zoneId in self.zoneVisDict:
            return self.zoneVisDict[zoneId]
        return []

    def getAvatars(self, clientChannel):
        def handleAvRetrieveDone(avList, avatarFields):
            # Prepare the potential avatar datagram for the client.
            resp = PyDatagram()
            resp.addUint16(5) # CLIENT_GET_AVATARS_RESP
            resp.addUint8(0) # returnCode
            resp.addUint16(len(avatarFields)) # avatarTotal

            for avId, fields in avatarFields.items():
                # Get the basic avatar fields the client needs.
                index = avList.index(avId)
                wishNameState = fields.get('WishNameState', [''])[0]
                name = fields['setName'][0]

                names = [name, '', '', '']
                allowedName = 0

                if wishNameState == 'OPEN':
                    allowedName = 1
                elif wishNameState == 'PENDING':
                    names[1] = name
                elif wishNameState == 'APPROVED':
                    names[2] = fields['WishName'][0]
                elif wishNameState == 'REJECTED':
                    names[3] = name

                resp.addUint32(avId) # avatarId

                resp.addString(name) # name
                resp.addString(names[1]) # wantName
                resp.addString(names[2]) # approvedName
                resp.addString(names[3]) # rejectedName

                resp.addBlob(fields['setDNAString'][0]) # avDNA
                resp.addUint8(index) # avPosition
                resp.addUint8(allowedName) # aName

            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addBlob(resp.getMessage())
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

    def filterBlacklist(self, doId, accId, message):
        avClientChannel = self.air.GetPuppetConnectionChannel(doId)
        flagged = None
        playToken = self.accId2playToken.get(accId)

        for word in message.split(' '):
            cleanWord = self.whiteList.cleanText(word).decode()

            if cleanWord in TTLocalizer.Blacklist:
                flagged = word
                break

        if not flagged:
            return False

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

            if self.isProdServer() and playToken:
                self.banAccount(playToken, message)

            del self.chatOffenses[doId]

        return True

    def checkBadName(self, name):
        divide = name.split(' ')
        lenStr = len(divide)
        s = 0

        while s != lenStr:
            name = divide[s]
            s += 1

        # Read our blacklist data.
        with open('game/resources/server/blacklist.txt', 'r') as badWordFile:
            data = badWordFile.readlines()

            for word in data:
                chrList = list(word)

                if chrList.count('\n') == 1:
                    chrList.remove('\n')

                badWord = ''.join(chrList)

                if name.lower() == badWord:
                    # This name is filthy.
                    return True

        # This name is not filthy.
        return False

    def checkWhitelistedName(self, name):
        divide = name.split(' ')
        lenStr = len(divide)
        s = 0

        while s != lenStr:
            name = divide[s]
            s += 1

        # Read our blacklist data.
        with open('game/resources/server/whitelist.txt', 'r') as wordFile:
            data = wordFile.readlines()

            for word in data:
                chrList = list(word)

                if chrList.count('\n') == 1:
                    chrList.remove('\n')

                whitelistedName = ''.join(chrList)

                if name.lower() == whitelistedName:
                    # This name is whitelisted.
                    return True

        # This name is not whitelisted.
        return False

    def packDetails(self, dclass, fields):
        # Pack required fields.
        fieldPacker = DCPacker()
        for i in range(dclass.getNumInheritedFields()):
            field = dclass.getInheritedField(i)
            if not field.isRequired() or field.asMolecularField():
                continue

            k = field.getName()
            v = fields.get(k, None)

            fieldPacker.beginPack(field)
            if not v:
                fieldPacker.packDefaultValue()
            else:
                field.packArgs(fieldPacker, v)

            fieldPacker.endPack()

        return fieldPacker.getBytes()

    def handleDatagram(self, dgi):
        """
        This handles datagrams coming directly from the Toontown 2013 client.
        These datagrams may be reformatted in a way that can appease Astron,
        or are totally game-specific and will have their own handling.
        """

        clientChannel = dgi.getUint64()

        try:
            msgType = dgi.getUint16()
        except:
            # Invalid datagram.
            errorCode = 122
            message = 'You have been ejected for attempting to send a incorrectly formatted datagram.'
            self.sendBoot(clientChannel, errorCode, message)
            self.sendEject(clientChannel, errorCode, message)
            return

        if msgType == 3: # CLIENT_GET_AVATARS
            self.getAvatars(clientChannel)
        elif msgType == 6: # CLIENT_CREATE_AVATAR
            echoContext = dgi.getUint16()
            dnaString = dgi.getBlob()
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
                dg.addBlob(resp.getMessage())
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

                # Put together the fields the avatar needs.
                # We don't need to put all of the DB
                # default values here as they are set in the DC file.
                toonFields = {'setName': (name,),
                              'WishNameState': ('OPEN',),
                              'WishName': ('',),
                              'setDNAString': (dnaString,),
                              'setDISLid': (target,)}

                # Create the Toon object.
                self.air.dbInterface.createObject(self.air.dbId,
                                                  self.air.dclassesByName['DistributedToonUD'],
                                                  toonFields,
                                                  lambda avId: handleCreate(oldAvList, avList, avId))

            # Query the account.
            self.air.dbInterface.queryObject(self.air.dbId, clientChannel >> 32, handleRetrieve)
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
                self.sendBoot(clientChannel, 122, message)
                self.sendEject(clientChannel, 122, message)
                return

            if self.isProdServer():
                try:
                    # Decrypt the play token.
                    key = binascii.unhexlify(self.playTokenDecryptKey)
                    encrypted = json.loads(base64.b64decode(playToken))
                    encryptedData = base64.b64decode(encrypted['data'])
                    iv = base64.b64decode(encrypted['iv'])
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    data = unpad(cipher.decrypt(encryptedData), AES.block_size)
                    jsonData = json.loads(data)

                    # Retrieve data from the API response.
                    playToken = str(jsonData['playToken'])
                    openChat = int(jsonData['OpenChat'])
                    isPaid = int(jsonData['Member'])
                    timestamp = jsonData['Timestamp']
                    dislId = int(jsonData['dislId'])
                    accountType = str(jsonData['accountType'])
                    linkedToParent = int(jsonData['LinkedToParent'])

                    if self.wantTokenExpirations and timestamp < int(time.time()):
                        errorCode = 122
                        message = 'Token has expired.'

                        self.sendBoot(clientChannel, errorCode, message)
                        self.sendEject(clientChannel, errorCode, message)
                        return
                except:
                    # Bad play token.
                    errorCode = 122
                    message = 'Invalid play token.'

                    self.sendBoot(clientChannel, errorCode, message)
                    self.sendEject(clientChannel, errorCode, message)
                    return

                # Send our webhook with some login information.
                fields = [{
                    'name': 'playToken',
                    'value': playToken,
                    'inline': True
                },
                {
                    'name': 'serverVersion',
                    'value': serverVersion,
                    'inline': True
                },
                {
                    'name': 'hashVal',
                    'value': hashVal,
                    'inline': True
                },
                {
                    'name': 'tokenType',
                    'value': tokenType,
                    'inline': True
                },
                {
                    'name': 'wantMagicWords',
                    'value': wantMagicWords,
                    'inline': True
                }]

                message = Webhook()
                message.setDescription('Someone is trying to login!')
                message.setFields(fields)
                message.setColor(1127128)
                message.setWebhook(config.GetString('discord-logins-webhook'))
                message.finalize()

                def callback(remoteIp, remotePort, localIp, localPort):
                    print(remoteIp)

                self.air.getNetworkAddress(self.air.getMsgSender(), callback)

                if accountType in ('Administrator', 'Developer', 'Moderator'):
                    # This is a staff member.
                    self.staffMembers[playToken] = accountType

                    accountId = self.bridge.query(playToken)

                    if accountId:
                        # This account is allowed to use Magic Words.
                        self.air.netMessenger.send('magicWordApproved', [accountId, accountType])

                if self.getStatus() == 1 and playToken not in self.staffMembers:
                    errorCode = 151
                    message = 'You have been logged out by an administrator working on the servers.'

                    self.sendBoot(clientChannel, errorCode, message)
                    self.sendEject(clientChannel, errorCode, message)
                    return
            else:
                # Production is not enabled.
                # We need these dummy variables.
                openChat = False
                isPaid = False
                dislId = 1
                linkedToParent = False

            # Check the server version against the real one.
            ourVersion = config.GetString('server-version', '')
            if serverVersion != ourVersion:
                # Version mismatch.
                reason = 'Client version mismatch: client=%s, server=%s' % (serverVersion, ourVersion)
                self.sendEject(clientChannel, 122, reason)
                return

            # Check the client DC hash against the server's DC hash.
            # Unfortunately, due to Python 3 we have to hardcode the hashVal.
            correctHashVal = 2308474396
            if hashVal != correctHashVal:
                # DC hash mismatch.
                reason = 'Client DC hash mismatch: client=%s, server=%s' % (hashVal, correctHashVal)
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
                    self.loginAccount(fields, clientChannel, accountId, playToken, openChat, isPaid, dislId, linkedToParent)

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
                self.loginAccount(account, clientChannel, accountId, playToken, openChat, isPaid, dislId, linkedToParent)

            # Create the Account in the database.
            self.air.dbInterface.createObject(self.air.dbId,
                                              self.air.dclassesByName['AccountUD'],
                                              account,
                                              createLoginResponse)
        elif msgType == 24: # CLIENT_OBJECT_UPDATE_FIELD
            # Certain fields need to be handled specifically...
            # The only example of this right now are setTalk and setTalkWhisper.
            doId = dgi.getUint32()
            fieldNumber = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

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

                accId = int(self.air.getAccountIdFromSender())
                playToken = self.accId2playToken.get(accId, '')

                if message[0] in ('~', '@'):
                    if playToken in self.staffMembers or not self.isProdServer():
                        # Route this to the Magic Word manager.
                        self.air.netMessenger.send('magicWord', [message, doId])
                        return

                blacklisted = self.filterBlacklist(doId, int(self.air.getAccountIdFromSender()), message)

                if blacklisted:
                    cleanMessage, modifications = '', []
                else:
                    cleanMessage, modifications = self.filterWhiteList(message)

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
                    return

                self.air.dbInterface.queryObject(self.air.dbId, avId, handleAvatar)

            resp = PyDatagram()
            resp.addServerHeader(clientChannel, self.air.ourChannel, CLIENT_OBJECT_SET_FIELD)
            resp.addUint32(doId)
            resp.addUint16(fieldNumber)
            resp.appendData(dcData)
            self.air.send(resp)
        elif msgType == 32: # CLIENT_SET_AVATAR
            avId = dgi.getUint32()

            if avId == 0:
                # We assume the avatar has logged out to the Pick A Toon.
                # Lets unload.

                # Grab the legitimate avId.
                currentAvId = self.air.getAvatarIdFromSender()

                # We need to send a NetMessenger hook.
                self.air.netMessenger.send('avatarOffline', [currentAvId])

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

                if self.isProdServer():
                    playToken = self.memberInfo.get(target, '')

                    if playToken:
                        # This account is a member.
                        access = OTPGlobals.AccessFull
                    else:
                        # This account is not a member.
                        access = OTPGlobals.AccessVelvetRope
                else:
                    if self.wantMembership:
                        access = OTPGlobals.AccessFull
                    else:
                        access = OTPGlobals.AccessVelvetRope

                activateFields = {
                    'setCommonChatFlags': [0],
                    'setAccess': [access]
                }

                # Activate the avatar on the DBSS.
                self.air.sendActivate(avId, 0, 0, self.air.dclassesByName['DistributedToonUD'], activateFields)

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
                    self.air.netMessenger.send('avatarOnline', [avId, x])

                # Assign a POST_REMOVE for an avatar that disconnects unexpectedly.
                cleanupDatagram = self.air.netMessenger.prepare('avatarOffline', [avId])

                datagram = PyDatagram()
                datagram.addServerHeader(channel, self.air.ourChannel, CLIENTAGENT_ADD_POST_REMOVE)
                datagram.addBlob(cleanupDatagram.getMessage())
                self.air.send(datagram)

                try:
                    # Tell the Party manager that we are online.
                    # [avatarId, accountId, playerName, playerNameApproved, openChatEnabled, createFriendsWithChat, chatCodeCreation]
                    self.air.partyManager.avatarOnlinePlusAccountInfo(avId, target, '', 1, 1, 1, 1)
                except:
                    # The MySQL database must of died.
                    self.notify.warning('Failed to call avatarOnlinePlusAccountInfo for Parties!')

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
            try:
                avId = dgi.getUint32()
                p1 = dgi.getInt16()
                f1 = dgi.getInt16()
                p2 = dgi.getInt16()
                f2 = dgi.getInt16()
                p3 = dgi.getInt16()
                f3 = dgi.getInt16()
                p4 = dgi.getInt16()
                f4 = dgi.getInt16()
            except:
                message = 'You have been ejected for attempting to send a incorrectly formatted datagram.'
                self.sendBoot(clientChannel, 122, message)
                self.sendEject(clientChannel, 122, message)
                return

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
                dg.addBlob(resp.getMessage())
                self.air.send(dg)

            # Query the avatar.
            self.air.dbInterface.queryObject(self.air.dbId, avId, handleRetrieve)
        elif msgType == 70: # CLIENT_SET_WISHNAME
            accountId = self.air.getAccountIdFromSender()

            try:
                avId = dgi.getUint32()
                name = dgi.getString()
            except:
                message = 'You have been ejected for attempting to send a incorrectly formatted datagram.'
                self.sendBoot(clientChannel, 122, message)
                self.sendEject(clientChannel, 122, message)
                return

            # If we have a avId, update the Avatar object with the new wish name.
            fields = {
                'WishNameState': ('PENDING',),
                'WishName': (name,)
                }

            if avId:
                self.air.dbInterface.updateObject(self.air.dbId, avId, self.air.dclassesByName['DistributedToonUD'], fields)

                valid = False

                if accountId in self.air.centralLogger.stateMap:
                    valid = self.air.centralLogger.stateMap[accountId]

                if self.isProdServer() and valid:
                    fields = [{
                        'name': 'Avatar Id',
                        'value': avId,
                        'inline': True
                    },
                    {
                        'name': 'Name',
                        'value': name,
                        'inline': True
                    },
                    {
                        'name': 'Server Type',
                        'value': ServerGlobals.FINAL_TOONTOWN,
                        'inline': True
                    }]

                    message = Webhook()
                    message.setDescription('A new toon has requested a typed name!')
                    message.setFields(fields)
                    message.setColor(1127128)
                    message.setWebhook(config.GetString('discord-approvals-webhook'))
                    message.finalize()

                    headers = {
                        'User-Agent': 'SunriseGames-ExtAgent'
                    }

                    data = {
                        'name': name,
                        'secretKey': self.rpcKey,
                        'avatarId': avId,
                        'serverName': ServerGlobals.serverToName[ServerGlobals.FINAL_TOONTOWN]
                    }

                    request = requests.post('https://sunrise.games/panel/names/approve.php', data, headers = headers).json()

            pendingName = name
            approvedName = ''
            rejectedName = ''

            # Check our name for any blacklisted words.
            isNameBlacklisted = self.checkBadName(name)

            if isNameBlacklisted:
                # This name has blacklisted words.
                pendingName = ''
                rejectedName = name

            # Check to see if this name is whitelisted.
            isNameWhitelisted = self.checkWhitelistedName(name)

            if isNameWhitelisted:
                # This name is whitelisted.
                pendingName = ''
                approvedName = name

            # Prepare the wish name response.
            resp = PyDatagram()
            resp.addUint16(71) # CLIENT_SET_WISHNAME_RESP
            resp.addUint32(avId)
            resp.addUint16(0) # returnCode
            resp.addString(pendingName) # pendingName
            resp.addString(approvedName) # approvedName
            resp.addString(rejectedName) # rejectedName

            # Send it.
            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addBlob(resp.getMessage())
            self.air.send(dg)

            # Reset the account state.
            self.air.centralLogger.stateMap[accountId] = False
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

                if branchId and zoneId != branchId and isPlayground or isCogHQ and loaderName not in ('safeZoneLoader', 'cogHQLoader'):
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
        elif msgType in (14, 81): # CLIENT_GET_AVATAR_DETAILS, CLIENT_GET_PET_DETAILS
            if msgType == 14:
                dclassName = 'DistributedToonUD'
                sendId = 15 # CLIENT_GET_AVATAR_DETAILS_RESP
            elif msgType == 81:
                dclassName = 'DistributedPetAI'
                sendId = 82 # CLIENT_GET_PET_DETAILS_RESP

            doId = dgi.getUint32()

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName[dclassName]:
                    return

                # Pack our data to go to the client.
                packedData = self.packDetails(dclass, fields)

                # Our details response.
                resp = PyDatagram()

                resp.addUint16(sendId)

                resp.addUint32(doId)
                resp.addUint8(0)
                resp.appendData(packedData)

                # Send it.
                dg = PyDatagram()
                dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
                dg.addBlob(resp.getMessage())
                self.air.send(dg)

            self.air.dbInterface.queryObject(self.air.dbId, doId, handleRetrieve)
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

                # We can now update the account with the new data. handleRemove is the
                # callback which will be called upon completion of updateObject.
                self.air.dbInterface.updateObject(self.air.dbId, target, self.air.dclassesByName['AccountUD'], newFields, oldFields, handleRemove)

                self.getAvatars(clientChannel)

            self.air.dbInterface.queryObject(self.air.dbId, target, handleRetrieve)
        elif msgType in (78, 123): # CLIENT_SYSTEM_MESSAGE, CLIENT_SYSTEMMESSAGE_AKNOWLEDGE
            try:
                message = dgi.getString()
            except:
                message = 'You have been ejected for attempting to send a incorrectly formatted datagram.'
                self.sendBoot(clientChannel, 122, message)
                self.sendEject(clientChannel, 122, message)
                return

            resp = PyDatagram()
            resp.addUint16(msgType)

            resp.addString(message)

            # Dispatch the response to the client.
            dg = PyDatagram()
            dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
            dg.addBlob(resp.getMessage())
            self.air.send(dg)
        elif msgType == 72: # CLIENT_SET_WISHNAME_CLEAR
            avatarId = dgi.getUint32()
            actionFlag = dgi.getUint8()

            def handleRetrieve(dclass, fields):
                toonDclass = self.air.dclassesByName['DistributedToonUD']

                if dclass != toonDclass:
                    # This is not an Avatar object.
                    self.sendEject(clientChannel, 122, 'An Avatar object was not retrieved.')
                    return

                if actionFlag == 1:
                    # This name was approved.
                    # Set their name.
                    fields = {
                        'WishNameState': ('',),
                        'WishName': ('',),
                        'setName': (fields['WishName'][0],)
                    }
                else:
                    # This name was rejected.
                    # Set them to the OPEN state so they can try again.
                    fields = {
                        'WishNameState': ('OPEN',),
                        'WishName': ('',)
                    }

                simbase.air.dbInterface.updateObject(simbase.air.dbId, avatarId, toonDclass, fields)

            # Query the avatar.
            self.air.dbInterface.queryObject(self.air.dbId, avatarId, handleRetrieve)
        elif msgType == 71: # CLIENT_SET_WISHNAME_RESP
            # This is called when someone tries to play with datagrams.
            errorCode = 288
            message = TTLocalizer.LogoutForced

            self.sendBoot(clientChannel, errorCode, message)
            self.sendEject(clientChannel, errorCode, message)
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

        if msgType == CLIENT_DONE_INTEREST_RESP:
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
            resp.addUint16(msgType)
            resp.addUint32(doId)
        else:
            self.notify.warning('Received unknown message type %s from Astron' % msgType)

        if not resp:
            return

        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addBlob(resp.getMessage())
        self.air.send(dg)
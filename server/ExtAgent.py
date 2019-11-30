from direct.distributed.PyDatagram import *
from direct.distributed.MsgTypes import *
from direct.directnotify.DirectNotifyGlobal import directNotify
from NameGenerator import NameGenerator
from ToonDNA import ToonDNA
import json, time, os
import random

class JSONBridge:

    def __init__(self):
        self.__bridgeFile = config.GetString('account-bridge-file', 'astron/databases/accounts.json')

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
        self.air.netMessenger.accept('registerShard', self, self.registerShard)

        self.shardInfo = {}

        self.nameGenerator = NameGenerator()
        self.bridge = JSONBridge()

        self.loadAvProgress = set()

        self.clientChannel2avId = {}
        self.clientChannel2shardId = {}
        self.clientChannel2context = {}
        self.clientChannel2contextZone = {}

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
                if dclass != self.air.dclassesByName['Account']:
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
            result = dna.makeFromNetString(dnaString)
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
                                                  self.air.dclassesByName['Account'],
                                                  {'ACCOUNT_AV_SET': newAvList},
                                                  {'ACCOUNT_AV_SET': oldAvList},
                                                  lambda fields: handleAvatarResp(avId, fields))

            def handleRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['Account']:
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
                name = dna.getToonName()

                # Pick a default shard.
                shardKeys = list(self.shardInfo.keys())
                if not shardKeys:
                    # There aren't available shards...
                    self.sendEject(clientChannel, 122, 'No Districts are available right now.')
                    return

                defaultShard = random.choice(shardKeys)

                # Put together the fields the avatar needs.
                # Thankfully, we don't need to put all of the DB
                # default values here as Disney left them in
                # Toontown 2003's production DC file.
                toonFields = {'setName': (name,),
                              'WishNameState': ('OPEN',),
                              'WishName': ('',),
                              'setDNAString': (dnaString,),
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
            # that the original 2003 client uses.
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
                    if dclass != self.air.dclassesByName['Account']:
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
                                              self.air.dclassesByName['Account'],
                                              account,
                                              createLoginResponse)
        elif msgType == 24: # CLIENT_OBJECT_UPDATE_FIELD
            # Certain fields need to be handled specially...
            # The only example of this right now is setChat.
            doId = dgi.getUint32()
            fieldNumber = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

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

            def handleAvatarRetrieve(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonUD']:
                    # This is not an Avatar object.
                    self.sendEject(clientChannel, 122, 'An Avatar object was not retrieved.')
                    return

                target = clientChannel >> 32
                channel = self.air.GetAccountConnectionChannel(target)

                # Save the account ID.
                self.loadAvProgress.add(target)

                # Activate the avatar on the DBSS.
                self.air.sendActivate(avId, fields['setDefaultShard'][0], 1,
                    self.air.dclassesByName['DistributedToonUD'],
                    {'setCommonChatFlags': [0]})

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
                if dclass != self.air.dclassesByName['Account']:
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
                name = self.nameGenerator.makeName(pattern)

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
        if msgType == CLIENT_EJECT:
            resp = PyDatagram()
            resp.addUint16(4) # CLIENT_GO_GET_LOST
            resp.addUint16(dgi.getUint16())
            resp.addString(dgi.getString())
        elif msgType == CLIENT_DONE_INTEREST_RESP:
            contextId = dgi.getUint32()
            handle = dgi.getUint16()

            # Check the context for the zone.
            if clientChannel not in self.clientChannel2contextZone:
                # This is invalid.
                return

            if contextId not in self.clientChannel2contextZone[clientChannel]:
                # This is invalid.
                self.notify.warning('Context %s not stored for client %s' % (contextId, clientChannel))
                return

            zoneId = self.clientChannel2contextZone[clientChannel][contextId]

            resp = PyDatagram()
            resp.addUint16(48) # CLIENT_DONE_SET_ZONE_RESP
            resp.addInt16(zoneId)

            # Delete the data.
            del self.clientChannel2contextZone[clientChannel][contextId]
        elif msgType == CLIENT_OBJECT_SET_FIELD:
            doId = dgi.getUint32()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            resp.addUint16(24) # CLIENT_OBJECT_UPDATE_FIELD
            resp.addUint32(doId)
            resp.appendData(dcData)
        elif msgType == CLIENT_OBJECT_LOCATION:
            pass
        elif msgType == CLIENT_OBJECT_LEAVING:
            doId = dgi.getUint32()

            resp = PyDatagram()
            resp.addUint16(25) # CLIENT_OBJECT_DISABLE_RESP
            resp.addUint32(doId)
        elif msgType == CLIENT_ENTER_OBJECT_REQUIRED:
            doId = dgi.getUint32()
            parentId = dgi.getUint32()
            zoneId = dgi.getUint32()
            classId = dgi.getUint16()
            dcData = dgi.getRemainingBytes()

            resp = PyDatagram()
            resp.addUint16(34) # CLIENT_CREATE_OBJECT_REQUIRED
            resp.addUint16(classId)
            resp.addUint32(doId)
            resp.appendData(dcData)
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
        else:
            self.notify.warning('Received unknown message type %s from Astron' % msgType)

        if not resp:
            return

        dg = PyDatagram()
        dg.addServerHeader(clientChannel, self.air.ourChannel, CLIENTAGENT_SEND_DATAGRAM)
        dg.addString(resp.getMessage())
        self.air.send(dg)
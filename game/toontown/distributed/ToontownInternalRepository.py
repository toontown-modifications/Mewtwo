from direct.distributed.AstronInternalRepository import AstronInternalRepository
from game.otp.distributed import OtpDoGlobals
from direct.distributed import MsgTypes
from direct.distributed.PyDatagram import PyDatagram
from game.otp.ai import AIMsgTypes

class ToontownInternalRepository(AstronInternalRepository):
    GameGlobalsId = OtpDoGlobals.OTP_DO_ID_TOONTOWN
    dbId = 4003

    def __init__(self, baseChannel, serverId = None, dcFileNames = None, dcSuffix = 'AI', connectMethod = None, threadedNet = None):
        AstronInternalRepository.__init__(self, baseChannel, serverId = serverId, dcFileNames = dcFileNames, dcSuffix = dcSuffix, connectMethod = connectMethod, threadedNet = threadedNet)

        if dcSuffix == 'UD':
            self.isUber = True
        else:
            self.isUber = False

    def handleConnected(self):
        AstronInternalRepository.handleConnected(self)

        self.netMessenger.register(3, 'avatarOnline')
        self.netMessenger.register(4, 'avatarOffline')

        if self.isUber:
            from game.toontown.uberdog.ExtAgent import ExtAgent

            self.extAgent = ExtAgent(self)

    def handleDatagram(self, dgi):
        msgType = self.getMsgType()

        if not msgType:
            return

        if msgType == 1205:
            self.extAgent.handleDatagram(dgi)
            return

        elif msgType == 1206:
            self.extAgent.handleResp(dgi)
            return

        AstronInternalRepository.handleDatagram(self, dgi)

    def getAvatarIdFromSender(self):
        return self.getMsgSender() & 0xFFFFFFFF

    def getAccountIdFromSender(self):
        return (self.getMsgSender() >> 32) & 0xFFFFFFFF

    def GetPuppetConnectionChannel(self, doId):
        return doId + (1001 << 32)

    def GetAccountConnectionChannel(self, doId):
        return doId + (1003 << 32)

    def GetAccountIDFromChannelCode(self, channel):
        return channel >> 32

    def GetAvatarIDFromChannelCode(self, channel):
        return channel & 0xffffffff

    def _isValidPlayerLocation(self, parentId, zoneId):
        if zoneId < 1000 and zoneId != 1:
            return False

        return True

    def setAllowClientSend(self, avId, dObj, fieldNameList = []):
        """
        Overrides the security of a field(s) specified, allows an owner of a DistributedObject to send
        the field(s) regardless if its marked ownsend/clsend.
        """

        dg = PyDatagram()
        dg.addServerHeader(dObj.GetPuppetConnectionChannel(avId), self.ourChannel, MsgTypes.CLIENTAGENT_SET_FIELDS_SENDABLE)
        fieldIds = []
        for fieldName in fieldNameList:
            field = dObj.dclass.getFieldByName(fieldName)
            if field:
                fieldIds.append(field.getNumber())
        dg.addUint32(dObj.getDoId())
        dg.addUint16(len(fieldIds))
        for fieldId in fieldIds:
            dg.addUint16(fieldId)
        self.send(dg)

    def createDgUpdateToDoId(self, dclassName, fieldName, doId, args,
                         channelId=None):
        """
        channelId can be used as a recipient if you want to bypass the normal
        airecv, ownrecv, broadcast, etc.  If you don't include a channelId
        or if channelId == doId, then the normal broadcast options will
        be used.

        This is just like sendUpdateToDoId, but just returns
        the datagram instead of immediately sending it.
        """
        result = None
        dclass=self.dclassesByName.get(dclassName+self.dcSuffix)
        assert dclass is not None
        if channelId is None:
            channelId=doId
        if dclass is not None:
            dg = dclass.aiFormatUpdate(
                    fieldName, doId, channelId, self.ourChannel, args)
            result = dg
        return result

    def addPostSocketClose(self, themessage):
        # Time to send a register for channel message to the msgDirector
        datagram = PyDatagram()
#        datagram.addServerControlHeader(CONTROL_ADD_POST_REMOVE)
        datagram.addInt8(1)
        datagram.addChannel(AIMsgTypes.CONTROL_MESSAGE)
        datagram.addUint16(MsgTypes.CONTROL_ADD_POST_REMOVE)

        datagram.addString(themessage.getMessage())
        self.send(datagram)

    def getSenderReturnChannel(self):
        return self.getMsgSender()
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from game.otp.distributed import OtpDoGlobals
from direct.distributed import MsgTypes
from direct.distributed.PyDatagram import PyDatagram

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

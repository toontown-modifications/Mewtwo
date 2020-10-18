class ServerBase:
    def __init__(self):
        self.serverType = config.GetString('server-type', 'dev')
        self.wantPartialProd = config.GetBool('want-partial-prod', False)

    def isProdServer(self):
        return self.serverType == 'prod'

    def isPartialProd(self):
        return self.wantPartialProd
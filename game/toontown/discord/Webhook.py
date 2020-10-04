from direct.directnotify.DirectNotifyGlobal import directNotify
import requests

class Webhook:
    notify = directNotify.newCategory('Webhook')

    def __init__(self):
        self.webhookUrl = config.GetString('discord-webhook-url')

        self.title = ''
        self.description = ''
        self.color = 0

    def setTitle(self, title):
        self.title = title

    def getTitle(self):
        return self.title

    def setDescription(self, description):
        self.description = description

    def getDescription(self):
        return self.description

    def setColor(self, color):
        self.color = color

    def getColor(self):
        return self.color

    def send(self):
        data = {
            'embeds': [
                {
                    'title': self.getTitle(),
                    'description': self.getDescription(),
                    'color': self.getColor()
                }
            ]
        }

        request = requests.post(self.webhookUrl, json = data)

        if request.status_code == 204:
            self.notify.info('Successfully sent webhook!')
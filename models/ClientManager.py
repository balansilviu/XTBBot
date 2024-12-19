from api.xtb_client import Client

class ClientManager:
    def __init__(self):
        self.client = Client()

    def GetClient(self):
        return self.client

from models.ClientManager import ClientManager
from models.StrategiesManager import StrategyManager

class AppManager:
    def __init__(self):
        self.clientManager = ClientManager()
        self.strategyManager = StrategyManager()

    def GetClientManager(self):
        return self.clientManager

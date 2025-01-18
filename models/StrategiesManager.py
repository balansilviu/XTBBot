from strategies.Strategy import Strategy

class StrategyManager:
    def __init__(self):
        self.strategies = []

    def AddStrategy(self, strategy):
        self.strategies.append(strategy)
        self.strategies[-1].run()

    def DeleteStrategy(self, index):
        self.strategies[index].stop()
        self.strategies.pop(index)
    
    def StopAllStrategies(self):
        for strategy in self.strategies:
            strategy.stop()
    

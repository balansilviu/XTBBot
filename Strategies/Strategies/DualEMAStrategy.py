from strategies.Strategy import Strategy
from ta.trend import EMAIndicator
import pandas as pd

class DualEMAStrategy(Strategy):
    def __init__(self, client, symbol, timeframe, volume=0.1):
        super().__init__(client, symbol, timeframe, volume)
        self.ema20 = 20
        self.ema60 = 60
        self.underLowestEma = False
        self.consecutiveNegativeCandles = 0
        self.inTrade = False
        

    def getHighestEma(self):
        # Calculează valorile EMA pentru perioadele specificate
        ema20_value = self.calculateEMA(self.ema20, self.timeframe)
        ema60_value = self.calculateEMA(self.ema60, self.timeframe)

        ema20_value = EMAIndicator()

        # Returnează EMA-ul cel mai mare
        highest_ema = max(ema20_value, ema60_value)
        return highest_ema

    def getLowestEma(self):
        # Calculează valorile EMA pentru perioadele specificate
        ema20_value = self.calculateEMA(self.ema20, self.timeframe)
        ema60_value = self.calculateEMA(self.ema60, self.timeframe)

        ema20_value = ta.EMA()

        # Returnează EMA-ul cel mai mic
        lowest_ema = min(ema20_value, ema60_value)
        return lowest_ema
        
    def crossDownEma(self):
        returnValue = False
        super().DEBUG_PRINT("crossDownEma()" + " - current open: " + str(super().getCurrentCandleOpen()) + ", lowest EMA: " + str(self.getLowestEma()) + ", current close: " + str(super().getCurrentCandleClose()))
        if super().getCurrentCandleOpen() > self.getLowestEma() and super().getCurrentCandleClose() < self.getLowestEma():
            returnValue = True
            super().DEBUG_PRINT("\033[37mCross down lowest EMA")
        return returnValue

    def buyCheck(self):

        returnValue = False

        if self.crossDownEma():
            self.consecutiveNegativeCandles = 0
            self.underLowestEma = True
            returnValue = False

        if self.underLowestEma:
            if super().getLastCandleClose() < self.getLowestEma() and super().getCurrentCandleClose() > self.getLowestEma():
                self.consecutiveNegativeCandles = 0
                self.underLowestEma = False
                return False
            
            if self.consecutiveNegativeCandles == 0:
                self.consecutiveNegativeCandles += 1

            if self.consecutiveNegativeCandles == 1:
                if super().getCurrentCandleClose() < super().getLastCandleClose():
                    self.consecutiveNegativeCandles = self.consecutiveNegativeCandles + 1
                    returnValue = False
                else:
                    self.consecutiveNegativeCandles = 0
                    returnValue = False

            if self.consecutiveNegativeCandles == 2:
                if super().getCurrentCandleClose() < super().getLastCandleClose():
                    returnValue = True
                else:
                    self.consecutiveNegativeCandles = 0
                    returnValue = False
        
        return returnValue 
        

    def closeCheck(self):
        returnValue = False
        if super().getLastCandleClose() < self.getHighestEma() and super().getCurrentCandleClose() > self.getHighestEma():
            returnValue = True
        return returnValue

    def newCandle(self):
        
        pass 
        # super().newCandle()  

        # if self.buyCheck() and not self.inTrade:
        #     # self.openTrade()
        #     super().DEBUG_PRINT("\033[32mOpen trade")
        #     self.inTrade = True
        # if self.closeCheck() and self.inTrade:
        #     # self.closeTrade()
        #     super().DEBUG_PRINT("\033[31mClose trade")
        #     self.inTrade = False

from strategies.Strategy import Strategy
from ta.trend import EMAIndicator
import ta
import pandas as pd
from enum import Enum

class Timeframe(Enum):
    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    D1 = 1440
    W1 = 10080
    MN = 43200

class PriceState(Enum):
    NOT_CONFIG = 0
    OVER_HIGH_EMA = 1
    BETWEEN_EMAS = 2
    UNDER_LOW_EMA = 3
    WAITING_SIGNAL = 4
    FIRST_BUY = 5
    SECOND_BUY = 6

class TransactionState(Enum):
    NOT_CONFIG = 0
    BUY = 1
    SELL = 2

class DualEMAStrategy(Strategy):
    def __init__(self, client, symbol, timeframe, volume=0.1):
        super().__init__(client, symbol, timeframe, volume)
        self.ema20 = 20
        self.ema60 = 60
        self.underLowestEma = False
        self.consecutiveNegativeCandles = 0
        self.inTrade = False
        self.priceState = PriceState.NOT_CONFIG
        self.transactionState = TransactionState.NOT_CONFIG 
        

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

    def pricesUpdates(self):
        current_price = super().getCurrentCandleClose()
        lowestEma = self.getLowestEma()
        highestEma = self.getHighestEma()
        if current_price > highestEma:
            self.priceState = PriceState.OVER_HIGH_EMA
        elif current_price < lowestEma:
            self.priceState = PriceState.UNDER_LOW_EMA
        else:
            self.priceState = PriceState.BETWEEN_EMAS
    
    def executeStrategy(self):
        super().DEBUG_PRINT("\033[37mCallback")
        self.dispatchPriceStateMachine()
        self.dispatchTransactionStateMachine()

    def dispatchPriceStateMachine(self):
        # Logic if the price is not configured
        if self.priceState == PriceState.NOT_CONFIG:
            super().DEBUG_PRINT("\033[37mNOT_CONFIG")
            

        # Logic if the price is over the highest EMA
        elif self.priceState == PriceState.OVER_HIGH_EMA:
            super().DEBUG_PRINT("\033[37mOVER_HIGH_EMA")
            if self.transactionState == TransactionState.BUY:
                self.transactionState = TransactionState.SELL

        # Logic if the price is between EMAs
        elif self.priceState == PriceState.BETWEEN_EMAS:
            super().DEBUG_PRINT("\033[37mBETWEEN_EMAS")

        # Logic if the price is under the lowest EMA
        elif self.priceState == PriceState.UNDER_LOW_EMA:
            super().DEBUG_PRINT("\033[37mUNDER_LOW_EMA")
            if self.priceState == PriceState.UNDER_LOW_EMA:
                self.priceState = PriceState.WAITING_SIGNAL

        # Wait for the signal to occur
        elif self.priceState == PriceState.WAITING_SIGNAL:
            super().DEBUG_PRINT("\033[37mWAITING_SIGNAL")
            if self.priceState == PriceState.UNDER_LOW_EMA:
                self.priceState = PriceState.FIRST_BUY

        # Logic if the pric
        elif self.priceState == PriceState.FIRST_BUY:
            super().DEBUG_PRINT("\033[37mFIRST_BUY")
            if self.transactionState == TransactionState.SELL:
                self.transactionState = TransactionState.BUY

 
        else:
            pass

        self.pricesUpdates()

    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.NOT_CONFIG:
            pass

        elif self.transactionState == TransactionState.BUY:
            super().DEBUG_PRINT("\033[32m==============BUY==============")
            self.openTrade()

        elif self.transactionState == TransactionState.SELL:
            super().DEBUG_PRINT("\033[31m==============SELL==============")
            self.closeTrade()
        else:
            pass


    def newCandle(self):  
        super().newCandle()
        self.executeStrategy()  


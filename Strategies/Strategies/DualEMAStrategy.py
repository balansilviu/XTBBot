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
    CROSS = 7

class TransactionState(Enum):
    WAITING = 0
    BUY = 1
    SELL = 2

class TransactionPermision(Enum):
    NOT_ALLOWED = 1
    ALLOWED = 2

class DualEMAStrategy(Strategy):
    def __init__(self, client, symbol, timeframe, volume=0.1):
        super().__init__(client, symbol, timeframe, volume)
        self.ema20 = 20
        self.ema60 = 60
        self.underLowestEma = False
        self.consecutiveNegativeCandles = 0
        self.inTrade = False
        self.priceState = PriceState.NOT_CONFIG
        self.transactionState = TransactionState.WAITING 
        self.transactionPermision = TransactionPermision.NOT_ALLOWED
        self.current_price = 0
        self.last_price = 0
        self.lowestEma = 0
        self.highestEma = 0
        

    def getHighestEma(self):
        # Calculează valorile EMA pentru perioadele specificate
        ema20_value = self.calculateEMA(self.ema20, self.timeframe)
        ema60_value = self.calculateEMA(self.ema60, self.timeframe)

        # Returnează EMA-ul cel mai mare
        highest_ema = max(ema20_value, ema60_value)
        return highest_ema

    def getLowestEma(self):
        # Calculează valorile EMA pentru perioadele specificate
        ema20_value = self.calculateEMA(self.ema20, self.timeframe)
        ema60_value = self.calculateEMA(self.ema60, self.timeframe)

        # Returnează EMA-ul cel mai mic
        lowest_ema = min(ema20_value, ema60_value)
        return lowest_ema
    

    def pricesUpdates(self):
        self.current_price = super().getCurrentCandleClose()
        self.lowestEma = self.getLowestEma()
        self.highestEma = self.getHighestEma()

    
    def executeStrategy(self):
        self.pricesUpdates()
        self.dispatchPriceStateMachine()
        self.dispatchTransactionStateMachine()

    def dispatchPriceStateMachine(self):
        self.printStates()
        # Logic if the price is not configured
        if self.priceState == PriceState.NOT_CONFIG:
            if self.current_price > self.highestEma:
                self.priceState = PriceState.OVER_HIGH_EMA
            elif self.current_price < self.lowestEma:
                self.priceState = PriceState.UNDER_LOW_EMA
            else:
                self.priceState = PriceState.BETWEEN_EMAS
        
        # Logic if the price is over the highest EMA
        elif self.priceState == PriceState.OVER_HIGH_EMA:
            if self.current_price > self.highestEma:
                self.priceState = PriceState.OVER_HIGH_EMA
            elif self.current_price < self.lowestEma:
                self.priceState = PriceState.WAITING_SIGNAL
            else:
                self.priceState = PriceState.BETWEEN_EMAS

            if self.transactionState == TransactionState.BUY:
                self.transactionState = TransactionState.SELL

            self.transactionState = TransactionPermision.ALLOWED

        # Logic if the price is between EMAs
        elif self.priceState == PriceState.BETWEEN_EMAS:
            if self.current_price > self.highestEma:
                self.priceState = PriceState.OVER_HIGH_EMA
            elif self.current_price < self.lowestEma:
                if self.transactionPermision == TransactionPermision.ALLOWED:
                    self.priceState = PriceState.WAITING_SIGNAL
                else:
                    self.priceState = PriceState.UNDER_LOW_EMA
            else:
                self.priceState = PriceState.BETWEEN_EMAS

        # Wait for the signal to occur
        elif self.priceState == PriceState.WAITING_SIGNAL:
            if self.current_price > self.highestEma:
                self.priceState = PriceState.OVER_HIGH_EMA
            elif self.current_price < self.lowestEma:
                self.priceState = PriceState.FIRST_BUY # Here is the the buy signal
            elif self.current_price > self.lowestEma:
                self.priceState = PriceState.BETWEEN_EMAS
            else:
                self.priceState = PriceState.UNDER_LOW_EMA

        # Logic if the price is under the lowest EMA
        elif self.priceState == PriceState.UNDER_LOW_EMA:
            if self.current_price > self.highestEma:
                self.priceState = PriceState.OVER_HIGH_EMA
            elif self.current_price < self.lowestEma:
                self.priceState = PriceState.UNDER_LOW_EMA
            else:
                self.priceState = PriceState.BETWEEN_EMAS

        # Logic if the pric
        elif self.priceState == PriceState.FIRST_BUY:
            if self.transactionState == TransactionState.WAITING:
                self.transactionState = TransactionState.BUY
                self.transactionPermision = TransactionPermision.NOT_ALLOWED
            if self.current_price > self.highestEma:
                self.priceState = PriceState.OVER_HIGH_EMA
            elif self.current_price < self.lowestEma:
                self.priceState = PriceState.UNDER_LOW_EMA
            else:
                self.priceState = PriceState.BETWEEN_EMAS
            

        else:
            pass
        
        self.last_price = self.current_price

    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.WAITING:
            pass

        elif self.transactionState == TransactionState.BUY:
            super().DEBUG_PRINT("\033[32m==============BUY==============")
            self.openTrade()

        elif self.transactionState == TransactionState.SELL:
            super().DEBUG_PRINT("\033[31m==============SELL==============")
            self.closeTrade()
            self.transactionState = TransactionState.WAITING
        
        else:
            pass

    def printStates(self):
        self.current_price = super().getCurrentCandleClose()
        self.lowestEma = self.getLowestEma()
        self.highestEma = self.getHighestEma()
        if self.priceState == PriceState.NOT_CONFIG:
            super().DEBUG_PRINT("\033[37mNOT_CONFIG - " + "Lowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))
            
        elif self.priceState == PriceState.OVER_HIGH_EMA:
            super().DEBUG_PRINT("\033[37mOVER_HIGH_EMA - " + "Lowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))

        elif self.priceState == PriceState.BETWEEN_EMAS:
            super().DEBUG_PRINT("\033[37mBETWEEN_EMAS - " + "Lowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))

        elif self.priceState == PriceState.UNDER_LOW_EMA:
            super().DEBUG_PRINT("\033[37mUNDER_LOW_EMA - " + "Lowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))

        elif self.priceState == PriceState.WAITING_SIGNAL:
            super().DEBUG_PRINT("\033[37mWAITING_SIGNAL - " + "Lowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))

        elif self.priceState == PriceState.FIRST_BUY:
            super().DEBUG_PRINT("\033[37mFIRST_BUY - " + "Lowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))
        else:
            pass


    def newCandle(self):  
        super().newCandle()
        self.executeStrategy()  


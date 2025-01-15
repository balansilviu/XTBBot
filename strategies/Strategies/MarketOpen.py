import datetime
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
    OVER_SMA = 1
    UNDER_SMA = 2

class TransactionState(Enum):
    WAITING = 0
    BUY = 1
    SELL = 2

class TransactionPermision(Enum):
    NOT_ALLOWED = 1
    ALLOWED = 2

class MarketOpen(Strategy):
    def __init__(self, client, symbol, timeframe, volume=0.3):
        super().__init__(client, symbol, timeframe, volume)
        self.sma = 20
        self.underLowestEma = False
        self.consecutiveNegativeCandles = 0
        self.inTrade = False
        self.priceState = PriceState.NOT_CONFIG
        self.transactionState = TransactionState.WAITING 
        self.transactionPermision = TransactionPermision.NOT_ALLOWED
        self.current_price = 0
        self.last_price = 0
        self.smaPrice = 0
        

    def getSMA(self):
        # Calculează valorile SMA pentru perioadele specificate
        sma = self.calculateSMA(self.sma, self.timeframe)

        return sma

    def pricesUpdates(self):
        self.current_price = super().getCurrentCandleClose()
        self.smaPrice = self.getSMA()

    
    def executeStrategy(self):
        self.pricesUpdates()
        self.dispatchPriceStateMachine()
        self.dispatchTransactionStateMachine()

    def dispatchPriceStateMachine(self):
        
        open_hour = 16
        open_minute = 30

        close_hour = 17
        close_minute = 00

        now = datetime.now()

        if now.weekday() in range(0, 5) and now.hour == open_hour and now.minute == open_minute:
            self.transactionState = TransactionState.BUY

        if now.weekday() in range(0, 5) and now.hour == close_hour and now.minute == close_minute:
            self.transactionState = TransactionState.SELL

        self.printStates()


        

    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.WAITING:
            pass
        elif self.transactionState == TransactionState.BUY:
            super().DEBUG_PRINT("\033[32m==============BUY===============")
            self.openTrade()

        elif self.transactionState == TransactionState.SELL:
            super().DEBUG_PRINT("\033[31m==============SELL==============")
            self.closeTrade()
        else:
            pass

    def printStates(self):
        if self.priceState == PriceState.NOT_CONFIG:
            super().DEBUG_PRINT("\033[37mNOT_CONFIG - SMA: " + str(round(self.smaPrice, 5)) + ", current close: " + str(self.current_price))
            
        elif self.priceState == PriceState.OVER_SMA:
            super().DEBUG_PRINT("\033[37mOVER_SMA - SMA: " + str(round(self.smaPrice, 5)) + ", current close: " + str(self.current_price))

        elif self.priceState == PriceState.UNDER_SMA:
            super().DEBUG_PRINT("\033[37mUNDER_SMA - SMA: " + str(round(self.smaPrice, 5)) + ", current close: " + str(self.current_price))
        
        else:
            pass

    def newCandle(self):  
        super().newCandle()
        self.executeStrategy()
        





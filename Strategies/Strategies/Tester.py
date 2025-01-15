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

class Tester(Strategy):
    def __init__(self, client, symbol, timeframe, volume=0.1):
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
        pass


        

    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.BUY:
            super().DEBUG_PRINT("\033[32m==============BUY===============")
            self.transactionState = TransactionState.TRADE_OPEN
            self.openTrade_stop_loss(self.currentLot, self.stopLoss_Pips)

        elif self.transactionState == TransactionState.SELL:
            super().DEBUG_PRINT("\033[31m==============SELL==============")
            self.transactionState = TransactionState.TRADE_CLOSED
            self.closeTrade()

            if self.wasLastTradeClosedByStopLoss():
                self.currentLot = self.currentLot * 2
                if self.currentLot >= self.maximumLot:
                    self.currentLot = self.maximumLot 
            else:
                self.currentLot = self.initialLot

        
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
        





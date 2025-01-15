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
    WAIT_CONFIRMATION = 4
    WAIT_TWO_NEGATIVES = 5

class TransactionState(Enum):
    BUY = 1
    SELL = 2
    TRADE_OPEN = 3
    TRADE_CLOSED = 4

class TransactionPermision(Enum):
    NOT_ALLOWED = 1
    ALLOWED = 2

class DualEMA_Martingale(Strategy):
    def __init__(self, client, symbol, timeframe, volume=0.1):
        super().__init__(client, symbol, timeframe, volume)
        self.ema20 = 9
        self.ema60 = 18
        self.underLowestEma = False
        self.consecutiveNegativeCandles = 0
        self.inTrade = False
        self.priceState = PriceState.NOT_CONFIG
        self.lastPriceState = PriceState.NOT_CONFIG
        self.transactionState = TransactionState.TRADE_CLOSED
        self.transactionPermision = TransactionPermision.ALLOWED
        self.current_price = 0
        self.last_price = 0
        self.lowestEma = 0
        self.highestEma = 0
        self.initialLot = 0.5
        self.currentLot = self.initialLot
        self.maximumLot = 2
        self.stopLoss_Pips = 10
        

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
        self.last_price = super().getLastCandleClose()
        self.lowestEma = self.getLowestEma()
        self.highestEma = self.getHighestEma()
        
        
        if self.current_price > self.highestEma:
            self.priceState = PriceState.OVER_HIGH_EMA
        elif self.current_price < self.lowestEma:
            self.priceState = PriceState.UNDER_LOW_EMA
        else:
            self.priceState = PriceState.BETWEEN_EMAS

    
    def executeStrategy(self):
        self.pricesUpdates()
        self.dispatchPriceStateMachine()
        self.dispatchTransactionStateMachine()

    def dispatchPriceStateMachine(self):
        if self.priceState == PriceState.OVER_HIGH_EMA:
            super().DEBUG_PRINT("\033mOVER_HIGH_EMA")
            self.transactionPermision = TransactionPermision.ALLOWED

            if self.lastPriceState == PriceState.BETWEEN_EMAS or self.lastPriceState == PriceState.UNDER_LOW_EMA:
                if self.transactionState == TransactionState.TRADE_OPEN:
                    self.transactionState = TransactionState.SELL
                

        elif self.priceState == PriceState.UNDER_LOW_EMA:
            
            if self.transactionPermision == TransactionPermision.NOT_ALLOWED:
                super().DEBUG_PRINT("\033mUNDER_LOW_EMA - Transaction not allowed")
            else:
                if self.lastPriceState == PriceState.BETWEEN_EMAS or self.lastPriceState == PriceState.OVER_HIGH_EMA:
                    self.priceState = PriceState.WAIT_CONFIRMATION
                    super().DEBUG_PRINT("\033mUNDER_LOW_EMA - CROSS - WAIT CONFIRMATION")
                
                elif self.lastPriceState == PriceState.WAIT_CONFIRMATION:
                    if self.current_price < self.last_price:
                        super().DEBUG_PRINT("\033mUNDER_LOW_EMA - BUY")
                        if self.transactionState == TransactionState.TRADE_CLOSED:
                            self.transactionState = TransactionState.BUY
                            self.transactionPermision = TransactionPermision.NOT_ALLOWED
                            self.priceState = PriceState.UNDER_LOW_EMA
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES
                        super().DEBUG_PRINT("\033mUNDER_LOW_EMA - WAIT TWO NEGATIVES")

                elif self.lastPriceState == PriceState.WAIT_TWO_NEGATIVES:
                    if self.current_price < self.last_price:
                        self.priceState == PriceState.WAIT_CONFIRMATION
                        super().DEBUG_PRINT("\033mUNDER_LOW_EMA - WAIT CONFIRMATION")
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES
                        super().DEBUG_PRINT("\033mUNDER_LOW_EMA - WAIT TWO NEGATIVES")

                else:
                    super().DEBUG_PRINT("\033mSTATE = " + str(self.priceState))
                    super().DEBUG_PRINT("\033mUNDER_LOW_EMA")

        else:
            super().DEBUG_PRINT("\033mBETWEEN_EMAS")

        self.lastPriceState = self.priceState


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
        
        # super().DEBUG_PRINT("\033[37mLowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))
        super().DEBUG_PRINT("\033mLowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", Current close: " + str(self.current_price) + ", Last close: " + str(self.last_price))
        


    def newCandle(self):  
        super().newCandle()
        self.executeStrategy()  


from strategies.Strategy import Strategy
from ta.trend import EMAIndicator
import ta
import pandas as pd
from enum import Enum
import time
from strategies.Strategy import MODES

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

class Timeframe_Seconds(Enum):
    M1 = 60
    M5 = 300
    M15 = 900
    M30 = 1800
    H1 = 3600
    H4 = 14400
    D1 = 86400
    W1 = 604800
    MN = 2592000

class PriceState(Enum):
    NOT_CONFIG = 0
    OVER_HIGH_EMA = 1
    BETWEEN_EMAS = 2
    UNDER_LOW_EMA = 3
    WAIT_CONFIRMATION = 4
    WAIT_TWO_NEGATIVES = 5
    WAIT_CONFIRMATION_CLOSE = 6
    WAIT_TWO_POSITIVES = 7


class TransactionState(Enum):
    BUY = 1
    SELL = 2
    TRADE_OPEN = 3
    TRADE_CLOSED = 4

class TransactionPermision(Enum):
    NOT_ALLOWED = 1
    ALLOWED = 2

class DualEMA_Martingale_H1_Working(Strategy):
    inTrade = False
    priceState = PriceState.NOT_CONFIG
    lastPriceState = PriceState.NOT_CONFIG
    transactionState = TransactionState.TRADE_CLOSED
    transactionPermision = TransactionPermision.ALLOWED
    lowestEma = 0
    highestEma = 0
    profit = 0
    queue_properties = False
    saved_properties = None
    atrToPipsMultiplier = 10000
    stopLoss = 0
    takeProfit = 0
    
    def __init__(self, client, symbol, fastEma=20, slowEma=50, atrLength=14, atrMultiplier=2):
        super().__init__(client, symbol)
        self.fastEma = fastEma
        self.slowEma = slowEma
        self.atrLength = atrLength
        self.atrMultiplier = atrMultiplier
        self.currentLot = self.volume

    def GetProperties(self):
        baseProperties = super().GetProperties()
        derivedProperties = {
            "FastEMA": self.fastEma,
            "SlowEMA": self.slowEma,
            "ATRLength": self.atrLength,
            "ATRMultiplier": self.atrMultiplier
        }
        return {**baseProperties, **derivedProperties}
    
    def SetProperties(self, **kwargs):
        if self.transactionState == TransactionState.TRADE_CLOSED:
            new_timeframe = int(kwargs["Timeframe"])
            if new_timeframe != self.timeframe:
                self.priceState = PriceState.NOT_CONFIG
            new_fastEma = int(kwargs["FastEMA"])
            if new_fastEma != self.fastEma:
                self.priceState = PriceState.NOT_CONFIG
            new_slowEma = int(kwargs["SlowEMA"])
            if new_slowEma != self.slowEma:
                self.priceState = PriceState.NOT_CONFIG
            
            super().SetProperties(**kwargs)
            self.maximumLot = 4 * self.volume
            if "FastEMA" in kwargs:
                self.fastEma = int(kwargs["FastEMA"])
            if "SlowEMA" in kwargs:
                self.slowEma = int(kwargs["SlowEMA"])
            if "ATRLength" in kwargs:
                self.atrLength = int(kwargs["ATRLength"])
            if "ATRMultiplier" in kwargs:
                self.atrMultiplier = int(kwargs["ATRMultiplier"])
            
        else:
            self.queue_properties = True
            self.saved_properties = kwargs

    def getHighestEma(self):
        fastEma_value = self.calculateEMA(self.fastEma, self.timeframe)
        slowEma_value = self.calculateEMA(self.slowEma, self.timeframe)

        highest_ema = max(fastEma_value, slowEma_value)
        return highest_ema

    def getLowestEma(self):
        fastEma_value = self.calculateEMA(self.fastEma, self.timeframe)
        slowEma_value = self.calculateEMA(self.slowEma, self.timeframe)

        lowest_ema = min(fastEma_value, slowEma_value)
        return lowest_ema
    
    def pricesUpdates(self):
        self.current_price = self.getLastCandleDetails(1)[0]['close']
        self.current_open = super().getCurrentCandleOpen()
        self.last_price = super().getLastCandleClose()
        self.lowestEma = self.getLowestEma()
        self.highestEma = self.getHighestEma()
        atrVal = self.calculateATR(self.atrLength, self.timeframe)
        self.stopLoss = round(atrVal * self.atrToPipsMultiplier * self.atrMultiplier, 1)
        self.takeProfit = 3 * round(atrVal * self.atrToPipsMultiplier * self.atrMultiplier, 1)
        
        if self.current_price > self.highestEma:
            self.priceState = PriceState.OVER_HIGH_EMA
        elif self.current_price < self.lowestEma:
            self.priceState = PriceState.UNDER_LOW_EMA
        else:
            self.priceState = PriceState.BETWEEN_EMAS

    def setLotSize(self):
        if self.firstSet == False:
            if self.WasLastTradeProfitable() == False:
                self.currentLot = self.currentLot + self.volume
                if self.currentLot >= self.maximumLot:
                    self.currentLot = self.maximumLot 
            else:
                self.currentLot = self.volume
        else:
            self.firstSet = False
            self.currentLot = self.volume

    def executeStrategy(self):
        self.pricesUpdates()
        self.dispatchPriceStateMachine()
        self.dispatchTransactionStateMachine()

    def dispatchPriceStateMachine(self):
        if self.priceState == PriceState.OVER_HIGH_EMA:
            if self.transactionState == TransactionState.TRADE_OPEN:
                if self.lastPriceState == PriceState.BETWEEN_EMAS or self.lastPriceState == PriceState.UNDER_LOW_EMA:
                    self.priceState = PriceState.WAIT_CONFIRMATION_CLOSE
                elif self.lastPriceState == PriceState.WAIT_CONFIRMATION_CLOSE:
                    if self.current_price >= self.current_open:
                        self.transactionState = TransactionState.SELL
                        self.priceState = PriceState.OVER_HIGH_EMA
                    else:
                        self.priceState = PriceState.WAIT_TWO_POSITIVES

                elif self.lastPriceState == PriceState.WAIT_TWO_POSITIVES:
                    if self.current_price >= self.current_open:
                        self.priceState = PriceState.WAIT_CONFIRMATION_CLOSE
                    else:
                        self.priceState = PriceState.WAIT_TWO_POSITIVES
                else:
                    pass
            else:
                self.priceState = PriceState.OVER_HIGH_EMA

            self.transactionPermision = TransactionPermision.ALLOWED
        elif self.priceState == PriceState.UNDER_LOW_EMA:
            if self.transactionPermision == TransactionPermision.NOT_ALLOWED:
                pass
            else:
                if self.lastPriceState == PriceState.BETWEEN_EMAS or self.lastPriceState == PriceState.OVER_HIGH_EMA:
                    self.priceState = PriceState.WAIT_CONFIRMATION
                elif self.lastPriceState == PriceState.WAIT_CONFIRMATION:
                    if self.current_price <= self.current_open:
                        if self.transactionState == TransactionState.TRADE_CLOSED:
                            self.transactionState = TransactionState.BUY
                            self.transactionPermision = TransactionPermision.NOT_ALLOWED
                            self.priceState = PriceState.UNDER_LOW_EMA
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES

                elif self.lastPriceState == PriceState.WAIT_TWO_NEGATIVES:
                    if self.current_price <= self.current_open:
                        self.priceState = PriceState.WAIT_CONFIRMATION
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES
                else:
                    pass
        else:
            pass
        self.lastPriceState = self.priceState
        super().DEBUG_PRINT("" + str(self.priceState) + ", " + str(self.transactionState) + ", close = " + str(self.current_price) + ", open = " + str(self.current_open) + ", volume = " + str(self.volume) + ", stop loss = " + str(self.stopLoss))

    def dispatchTransactionStateMachine(self):
        if self.transactionState == TransactionState.BUY:
            # self.setLotSize()
            super().DEBUG_PRINT("============== BUY " + str(self.currentLot) + " ===============")
            self.transactionState = TransactionState.TRADE_OPEN
            self.openTrade_SL_TP(MODES.BUY.value, self.currentLot, self.stopLoss, self.takeProfit)

        elif self.transactionState == TransactionState.SELL:
            if self.ThereIsTransactionOpen() == True:
                self.transactionState = TransactionState.TRADE_CLOSED
                self.closeTrade()
                time.sleep(3)
                trade_profit = round(self.GetProfitOfLastTrade(), 2)
                self.profit = self.profit + self.GetProfitOfLastTrade()
                super().DEBUG_PRINT("============= SELL " + str(self.currentLot) + ", Profit = " + str(trade_profit) + " ===============")
                super().DEBUG_PRINT("TOTAL PROFIT = " + str(round(self.profit, 2)))
            else:
                pass
        elif self.transactionState == TransactionState.TRADE_CLOSED:
            if self.queue_properties == True:
                self.SetProperties(self.saved_properties)
                self.queue_properties = False
                
            if self.ThereIsTransactionOpen() == True:
                self.transactionState = TransactionState.TRADE_OPEN

        elif self.transactionState == TransactionState.TRADE_OPEN:
            if self.ThereIsTransactionOpen() == False:
                self.transactionState = TransactionState.TRADE_CLOSED
                trade_profit = round(self.GetProfitOfLastTrade(), 2)
                self.profit = self.profit + self.GetProfitOfLastTrade()
                super().DEBUG_PRINT("============= STOP LOSS " + str(self.currentLot) + ", Profit = " + str(trade_profit) + " ===============")
                super().DEBUG_PRINT("TOTAL PROFIT = " + str(round(self.profit, 2)))
        else:
            pass



    def newCandle(self):  
        super().newCandle()
        self.executeStrategy() 



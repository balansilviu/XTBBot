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

class TransactionState(Enum):
    BUY = 1
    SELL = 2
    TRADE_OPEN = 3
    TRADE_CLOSED = 4

class TransactionPermision(Enum):
    NOT_ALLOWED = 1
    ALLOWED = 2

class DualEMA_Martingale(Strategy):
    inTrade = False
    priceState = PriceState.NOT_CONFIG
    lastPriceState = PriceState.NOT_CONFIG
    transactionState = TransactionState.TRADE_CLOSED
    transactionPermision = TransactionPermision.NOT_ALLOWED
    lowestEma = 0
    highestEma = 0
    profit = 0
    queue_properties = False
    saved_properties = None
    
    def __init__(self, client, symbol, ema1=20, ema2=60):
        super().__init__(client, symbol)
        self.ema1 = ema1
        self.ema2 = ema2
        self.currentLot = self.volume
        self.maximumLot = 4 * self.volume

    def GetProperties(self):
        baseProperties = super().GetProperties()
        derivedProperties = {
            "EMA1": self.ema1,
            "EMA2": self.ema2
        }
        return {**baseProperties, **derivedProperties}
    
    def SetProperties(self, **kwargs):
        if self.transactionState == TransactionState.TRADE_CLOSED:
            new_timeframe = int(kwargs["Timeframe"])
            if new_timeframe != self.timeframe:
                self.priceState = PriceState.NOT_CONFIG
            new_ema1 = int(kwargs["EMA1"])
            if new_ema1 != self.ema1:
                self.priceState = PriceState.NOT_CONFIG
            new_ema2 = int(kwargs["EMA2"])
            if new_ema2 != self.ema2:
                self.priceState = PriceState.NOT_CONFIG
            
            super().SetProperties(**kwargs)
            if "EMA1" in kwargs:
                self.ema1 = int(kwargs["EMA1"])
            if "EMA2" in kwargs:
                self.ema2 = int(kwargs["EMA2"])
        else:
            self.queue_properties = True
            self.saved_properties = kwargs

    def getHighestEma(self):
        # Calculează valorile EMA pentru perioadele specificate
        ema1_value = self.calculateEMA(self.ema1, self.timeframe)
        ema2_value = self.calculateEMA(self.ema2, self.timeframe)

        # Returnează EMA-ul cel mai mare
        highest_ema = max(ema1_value, ema2_value)
        return highest_ema

    def getLowestEma(self):
        # Calculează valorile EMA pentru perioadele specificate
        ema1_value = self.calculateEMA(self.ema1, self.timeframe)
        ema2_value = self.calculateEMA(self.ema2, self.timeframe)

        # Returnează EMA-ul cel mai mic
        lowest_ema = min(ema1_value, ema2_value)
        return lowest_ema
    
    def pricesUpdates(self):
        self.current_price = self.getLastCandleDetails(1)[0]['close']
        self.current_open = super().getCurrentCandleOpen()
        self.last_price = super().getLastCandleClose()
        self.lowestEma = self.getLowestEma()
        self.highestEma = self.getHighestEma()
        
        
        if self.current_price > self.highestEma:
            self.priceState = PriceState.OVER_HIGH_EMA
        elif self.current_price < self.lowestEma:
            self.priceState = PriceState.UNDER_LOW_EMA
        else:
            self.priceState = PriceState.BETWEEN_EMAS

    def setLotSize(self):
        if self.WasLastTradeProfitable() == False:
            self.currentLot = self.currentLot * 2
            if self.currentLot >= self.maximumLot:
                self.currentLot = self.maximumLot 
        else:
            self.currentLot = self.volume

    def executeStrategy(self):
        self.pricesUpdates()
        self.dispatchPriceStateMachine()
        # if self.transactionState == TransactionState.TRADE_CLOSED:
        #     self.transactionState = TransactionState.BUY
        # if self.transactionState == TransactionState.TRADE_OPEN:
        #     self.transactionState = TransactionState.SELL
        self.dispatchTransactionStateMachine()

        print("Current lot = " + str(self.currentLot))
        print("volume = " + str(self.volume))

    def dispatchPriceStateMachine(self):
        if self.priceState == PriceState.OVER_HIGH_EMA:
            self.transactionPermision = TransactionPermision.ALLOWED
            if self.lastPriceState == PriceState.BETWEEN_EMAS or self.lastPriceState == PriceState.UNDER_LOW_EMA:
                if self.transactionState == TransactionState.TRADE_OPEN:
                    self.transactionState = TransactionState.SELL   
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
        super().DEBUG_PRINT("" + str(self.priceState) + ", " + str(self.transactionState) + ", close = " + str(self.current_price) + ", open = " + str(self.current_open) + ", low_ema = " + str(round(self.lowestEma, 5)) + ", high_ema = " + str(round(self.highestEma, 5)))

    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.BUY:
            self.setLotSize()
            super().DEBUG_PRINT("============== BUY " + str(self.currentLot) + " ===============")
            self.transactionState = TransactionState.TRADE_OPEN
            self.openTrade_stop_loss(self.currentLot, self.stopLoss)

        elif self.transactionState == TransactionState.SELL:
            if self.ThereIsTransactionOpen() == True:
                super().DEBUG_PRINT("============= SELL " + str(self.currentLot) + " ===============")
                self.transactionState = TransactionState.TRADE_CLOSED
                self.closeTrade()
            
                self.profit = self.profit + self.GetProfitOfLastTrade()
                super().DEBUG_PRINT("Profit = " + str(round(self.profit, 2)))
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
                super().DEBUG_PRINT("============= STOP LOSS " + str(self.currentLot) + " ===============")
                self.profit = self.profit + self.GetProfitOfLastTrade()
                super().DEBUG_PRINT("Profit = " + str(round(self.profit, 2)))
        else:
            pass

    def newCandle(self):  
        super().newCandle()
        self.executeStrategy() 



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
    def __init__(self, client, symbol, timeframe, volume=0.1):
        super().__init__(client, symbol, timeframe, volume)
        self.ema20 = 20
        self.ema60 = 60
        self.inTrade = False
        self.priceState = PriceState.NOT_CONFIG
        self.lastPriceState = PriceState.NOT_CONFIG
        self.transactionState = TransactionState.TRADE_CLOSED
        self.transactionPermision = TransactionPermision.NOT_ALLOWED
    
        self.lowestEma = 0
        self.highestEma = 0
        self.initialLot = 0.25
        self.currentLot = self.initialLot
        self.maximumLot = 2
        self.profit = 0
        
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
                    if self.current_price <= self.last_price:
                        if self.transactionState == TransactionState.TRADE_CLOSED:
                            self.transactionState = TransactionState.BUY
                            self.transactionPermision = TransactionPermision.NOT_ALLOWED
                            self.priceState = PriceState.UNDER_LOW_EMA
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES

                elif self.lastPriceState == PriceState.WAIT_TWO_NEGATIVES:
                    if self.current_price <= self.last_price:
                        self.priceState = PriceState.WAIT_CONFIRMATION
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES
                else:
                    pass
        else:
            pass
        self.lastPriceState = self.priceState
        super().DEBUG_PRINT("\033m" + str(self.priceState))

    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.BUY:
            super().DEBUG_PRINT("\033m============== BUY " + str(self.currentLot) + " ===============")
            self.transactionState = TransactionState.TRADE_OPEN
            self.openTrade_stop_loss(self.currentLot, self.stopLoss_Pips)

        elif self.transactionState == TransactionState.SELL:
            if self.ThereIsTransactionOpen() == True:
                super().DEBUG_PRINT("\033m============= SELL " + str(self.currentLot) + " ===============")
                self.transactionState = TransactionState.TRADE_CLOSED
                self.closeTrade()
                if self.WasLastTradeProfitable() == False:
                    self.currentLot = self.currentLot * 2
                    if self.currentLot >= self.maximumLot:
                        self.currentLot = self.maximumLot 
                else:
                    self.currentLot = self.initialLot

                self.profit = self.profit + self.GetProfitOfLastTrade()

                if self.profit > 0: 
                    super().DEBUG_PRINT("\033[32mProfit = " + str(round(self.profit, 2)))
                else:
                    super().DEBUG_PRINT("\033[31mProfit = " + str(round(self.profit, 2)))


            else:
                pass
        elif self.transactionState == TransactionState.TRADE_CLOSED:
            if self.ThereIsTransactionOpen() == True:
                self.transactionState = TransactionState.TRADE_OPEN

        elif self.transactionState == TransactionState.TRADE_OPEN:
            if self.ThereIsTransactionOpen() == False:
                self.transactionState = TransactionState.TRADE_CLOSED
                super().DEBUG_PRINT("\033m============= STOP LOSS " + str(self.currentLot) + " ===============")

                self.profit = self.profit + self.GetProfitOfLastTrade()

                self.currentLot = self.currentLot * 2
                if self.currentLot >= self.maximumLot:
                    self.currentLot = self.maximumLot
                
                if self.profit > 0: 
                    super().DEBUG_PRINT("\033[32mProfit = " + str(round(self.profit, 2)))
                else:
                    super().DEBUG_PRINT("\033[31mProfit = " + str(round(self.profit, 2)))
        
        else:
            pass

    def newCandle(self):  
        super().newCandle()

        self.pricesUpdates()
        # self.DEBUG_PRINT("Close = " + str(self.current_price) + ", last = " + str(self.last_price) + ", low_ema = " + str(round(self.lowestEma, 5)) + ", high_ema = " + str(round(self.highestEma, 5)))

        self.executeStrategy()  



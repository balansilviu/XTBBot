from strategies.Strategy import Strategy
from ta.trend import EMAIndicator
import ta
import pandas as pd
from enum import Enum
from strategies import Indicators
from datetime import datetime, timezone, timedelta


PIP_Multiplier = {
    "EURUSD":0.0001
}

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

class DualEMA_Martingale_Tester(Strategy):
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
        self.stopLoss_Pips = 2.5
        self.low = 0
        
        self.iteration = 0
        self.current_price_arr = []
        self.last_price_arr = []
        self.ema20_arr = []
        self.ema60_arr = []
        self.low_arr = []
        self.time_arr = []
        self.profit = 0
        self.spread = 0.9
        self.open_price = 0
        self.pip_value = 4.86
        self.last_profit = 0
        self.trasactionOpen = False
        

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
    

    def pricesUpdates(self, iteration):
        self.current_price = self.current_price_arr[iteration]
        self.last_price = self.last_price_arr[iteration]

        if self.ema20_arr[iteration] < self.ema60_arr[iteration]:
            self.lowestEma = self.ema20_arr[iteration]
            self.highestEma = self.ema60_arr[iteration]
        else:
            self.lowestEma = self.ema60_arr[iteration]
            self.highestEma = self.ema20_arr[iteration]
        self.low = self.low_arr[iteration]
        
        if self.current_price > self.highestEma:
            self.priceState = PriceState.OVER_HIGH_EMA
        elif self.current_price < self.lowestEma:
            self.priceState = PriceState.UNDER_LOW_EMA
        else:
            self.priceState = PriceState.BETWEEN_EMAS

    
    def executeStrategy(self, iteration):
        self.pricesUpdates(iteration)
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
                    if self.current_price < self.last_price:
                        if self.transactionState == TransactionState.TRADE_CLOSED:
                            self.transactionState = TransactionState.BUY
                            self.transactionPermision = TransactionPermision.NOT_ALLOWED
                            self.priceState = PriceState.UNDER_LOW_EMA
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES

                elif self.lastPriceState == PriceState.WAIT_TWO_NEGATIVES:
                    if self.current_price < self.last_price:
                        self.priceState = PriceState.WAIT_CONFIRMATION
                    else:
                        self.priceState = PriceState.WAIT_TWO_NEGATIVES
                else:
                    pass
        else:
            pass
        # super().DEBUG_PRINT("\033m" + str(self.priceState))
        self.lastPriceState = self.priceState

    def dispatchTransactionStateMachine(self):

        # Transaction dispatch states
        if self.transactionState == TransactionState.BUY:
            super().DEBUG_PRINT("\033m============== BUY " + str(self.currentLot) + " ===============")
            self.transactionState = TransactionState.TRADE_OPEN
            self.trasactionOpen = True
            self.open_price = self.current_price
            self.openTrade_stop_loss(self.currentLot, self.stopLoss_Pips)

        elif self.transactionState == TransactionState.SELL:
            if self.inTrade == True:
                super().DEBUG_PRINT("\033m============= SELL " + str(self.currentLot) + " ===============")
                self.transactionState = TransactionState.TRADE_CLOSED
                self.closeTrade()
                
                self.profit = self.profit + (((self.current_price - self.open_price)/PIP_Multiplier[self.symbol] - self.spread) * self.pip_value)  * (self.currentLot / self.initialLot)
                if self.profit > 0: 
                    super().DEBUG_PRINT("\033[32mProfit = " + str(round(self.profit, 2)))
                else:
                    super().DEBUG_PRINT("\033[31mProfit = " + str(round(self.profit, 2)))

                if self.profit < self.last_profit:
                    self.currentLot = self.currentLot * 2
                    if self.currentLot >= self.maximumLot:
                        self.currentLot = self.maximumLot 
                else:
                    self.currentLot = self.initialLot

                self.last_profit = self.profit
                    
            else:
                pass
           
        elif self.transactionState == TransactionState.TRADE_CLOSED:
            pass
        elif self.transactionState == TransactionState.TRADE_OPEN:
            self.CheckForStopLoss()
            if self.wasLastTradeClosedByStopLoss():
                self.transactionState = TransactionState.TRADE_CLOSED
                super().DEBUG_PRINT("\033m============= STOP LOSS " + str(self.currentLot) + " ===============")
                
                self.currentLot = self.currentLot * 2
                if self.currentLot >= self.maximumLot:
                    self.currentLot = self.maximumLot 
                
                self.profit = self.profit - ((self.stopLoss_Pips - self.spread) * self.pip_value) * (self.currentLot / self.initialLot)
                if self.profit > 0: 
                    super().DEBUG_PRINT("\033[32mProfit = " + str(round(self.profit, 2)) + "\033m = > New lot size = " + str(self.currentLot))
                else:
                    super().DEBUG_PRINT("\033[31mProfit = " + str(round(self.profit, 2)) + "\033m = > New lot size = " + str(self.currentLot))

                

        else:
            pass

    def wasLastTradeClosedByStopLoss(self):
        return self.inTrade == False

    def CheckForStopLoss(self):
        if self.low <= self.open_price - (self.stopLoss_Pips - self.spread) * PIP_Multiplier[self.symbol]:
            self.inTrade = False

    def openTrade_stop_loss(self, volume=0.1, stop_loss=0):
        self.inTrade = True

    def closeTrade(self):
        pass

    def Test(self):

        # self.BACKTEST = True

        # backtest_period = 6000

        # self.current_price_arr = super().TEST_CURRENT_CLOSE_LAST_N_VALUES(backtest_period+1)
        # self.last_price_arr = super().TEST_LAST_CLOSE_LAST_N_VALUES(backtest_period+1)
        # self.ema20_arr = super().TEST_EMA_LAST_N_VALUES(backtest_period+1, self.ema20)
        # self.ema60_arr = super().TEST_EMA_LAST_N_VALUES(backtest_period+1, self.ema60)
        # self.time_arr = super().TEST_CURRENT_TIME_N_VALUES(backtest_period)
        # self.low_arr = super().TEST_CURRENT_LOW_LAST_N_VALUES(backtest_period + 1)

        # for i in range(1, backtest_period):
        #     self.time = self.time_arr[i]
        #     self.executeStrategy(i)
        #     pass

        print(self.getLastTimestamp())

    def newCandle(self):  
        pass


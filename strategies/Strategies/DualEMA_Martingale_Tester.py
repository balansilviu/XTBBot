from strategies.Strategy import Strategy
from ta.trend import EMAIndicator
import ta
import pandas as pd
from enum import Enum
from strategies import Indicators
from datetime import datetime, timezone, timedelta

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
        self.stopLoss_Pips = 10
        
        self.iteration = 0
        self.current_price_arr = []
        self.last_price_arr = []
        self.ema20_arr = []
        self.ema60_arr = []
        self.time = ""
        self.time_arr = []
        

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
            self.DEBUG_PRINT("\033mOVER_HIGH_EMA")
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

        self.lastPriceState = self.priceState
        self.DEBUG_PRINT(self.priceState)


    def dispatchTransactionStateMachine(self):
        # Transaction dispatch states
        if self.transactionState == TransactionState.BUY:
            self.DEBUG_PRINT("\033[32m==============BUY===============")
            self.transactionState = TransactionState.TRADE_OPEN
            # self.openTrade_stop_loss(self.currentLot, self.stopLoss_Pips)

        elif self.transactionState == TransactionState.SELL:
            self.DEBUG_PRINT("\033[31m==============SELL==============")
            self.transactionState = TransactionState.TRADE_CLOSED
            # self.closeTrade()

            if self.wasLastTradeClosedByStopLoss():
                self.currentLot = self.currentLot * 2
                if self.currentLot >= self.maximumLot:
                    self.currentLot = self.maximumLot 
            else:
                self.currentLot = self.initialLot

        
        else:
            pass

    def printStates(self):
        
        # self.DEBUG_PRINT("\033[37mLowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", current close: " + str(self.current_price))
        self.DEBUG_PRINT("\033mLowest EMA: " + str(round(self.lowestEma, 4)) + ", highest EMA: " + str(round(self.highestEma, 4)) + ", Current close: " + str(self.current_price) + ", Last close: " + str(self.last_price))
        
    
    def CURRENT_TIME_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length)
        timestamps = self.extractLabelValues(candle_history, "timestamp")

        gmt_plus_2 = timezone(timedelta(hours=2))


        formatted_times = [
            datetime.fromtimestamp(ts, gmt_plus_2).strftime('%Y-%m-%d %H:%M:%S')
            for ts in timestamps
        ]

        return formatted_times
    
    
    def CURRENT_CLOSE_LAST_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length)
        return self.extractLabelValues(candle_history, "close")
    
    def LAST_CLOSE_LAST_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length+1)
        arr = self.extractLabelValues(candle_history, "close")
        arr.pop()
        return arr

    def EMA_LAST_N_VALUES(self, length, ema_period):
        close_array = self.CURRENT_CLOSE_LAST_N_VALUES(length + 3*ema_period)
        
        arr = []

        for i in range(length):
            close_array_i = close_array[i+1:3*ema_period+i+1]
            ema = Indicators.EMA(close_array_i, ema_period)
            arr.append(round(float(ema), 5))

        return arr

    def Test(self):

        backtest_period = 1000

        self.current_price_arr = self.CURRENT_CLOSE_LAST_N_VALUES(backtest_period+1)
        self.last_price_arr = self.LAST_CLOSE_LAST_N_VALUES(backtest_period+1)
        self.ema20_arr = self.EMA_LAST_N_VALUES(backtest_period+1, self.ema20)
        self.ema60_arr = self.EMA_LAST_N_VALUES(backtest_period+1, self.ema60)
        self.time_arr = self.CURRENT_TIME_N_VALUES(backtest_period)

        print(self.time_arr)

        for i in range(1, backtest_period):
            self.time = self.time_arr[i]
            self.executeStrategy(i)
            pass

    def DEBUG_PRINT(self, text):
        reset_color = "\033[0m"  # Codul ANSI pentru resetarea culorii
        print(f"{self.time} DEBUG PRINT: {text}{reset_color}")

    def newCandle(self):  
        pass


import threading
import datetime
import asyncio
from strategies import Indicators
from enum import Enum
from api.xtb_api import MODES
from datetime import datetime, timezone, timedelta
import pytz
import os
import re

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

class Strategy:

    thread = None
    process = None
    lastCandle = 0
    currentCandle = 0
    stop_event = threading.Event()
    openTradeCount = 0
    appRetryConnectCount = 0
    current_price = 0
    current_open = 0
    last_price = 0
    timestamp = 0
    bid = 0
    BACKTEST = False
    time = ""
    logFile = ""
    firstSet = True

    def __init__(self, client, symbol, timeframe=1, stopLoss=10, volume=0.03):
        self.client = client
        self.symbol = symbol
        self.timeframe = timeframe
        self.stopLoss = stopLoss
        self.volume = volume
    
    def GetProperties(self):
        return {
            "Symbol": self.symbol,
            "Timeframe": self.timeframe,
            "StopLoss": self.stopLoss,
            "Volume": self.volume
        }
    
    def SetProperties(self, **kwargs):
        if "Symbol" in kwargs:
            self.symbol = kwargs["Symbol"]
        if "Timeframe" in kwargs:
            self.timeframe = int(kwargs["Timeframe"])
        if "StopLoss" in kwargs:
            self.stopLoss = float(kwargs["StopLoss"])
        if "Volume" in kwargs:
            self.volume = float(kwargs["Volume"])

    def SetLogFile(self, filename):
        self.logFile = filename

    def GetLogFile(self):
        return self.logFile

    def run_strategy(self):
        asyncio.run(self.__tick(1))

    def run(self):
        """Run the trading strategy in a separate thread"""
        self.thread = threading.Thread(target=self.run_strategy)
        self.thread.start()

    def stop(self):
        """Signal the thread to stop and wait for it to finish"""
        self.stop_event.set()  # Semnalizează oprirea
        self.thread.join()  # Așteaptă finalizarea thread-ului

    def getLastCandleDetails(self, timeframe_in_minutes):
        candle_history = []
        candle_history = self.client.get_lastn_candle_history(self.symbol, timeframe_in_minutes * 60, 1)
        return candle_history
    
    def getNLastCandleDetails(self, timeframe_in_minutes, n):
        candle_history = []
        candle_history = self.client.get_lastn_candle_history(self.symbol, timeframe_in_minutes * 60, n)
        return candle_history
    
    def getLastClosedTradeDetails(self):
        return self.client.get_last_closed_trade()

    def WasLastTradeProfitable(self):
        ret = False
        if self.getLastClosedTradeDetails()["profit"] >= 0:
            ret = True
        return ret
    
    def GetProfitOfLastTrade(self):
        ret = False
        return self.getLastClosedTradeDetails()["profit"]

    def wasLastTradeClosedByStopLoss(self):
        ret = False
        if self.getLastClosedTradeDetails()["comment"] == "[S/L]":
            ret = True
        return ret

    def getNLastCandlesDetails(self, timeframe_in_minutes, number_of_candles):
        candle_history = []
        candle_history = self.client.get_lastn_candle_history(self.symbol, timeframe_in_minutes * 60, number_of_candles)
        return candle_history
    
    def calculateEMA(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, 3 * period)
        close_extracted = self.extractLabelValues(candle_history, "close")
        return Indicators.EMA(close_extracted, period)
    
    def calculateSMA(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return Indicators.SMA(self.extractLabelValues(candle_history, "close"), period)

    def calculateRSI(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return Indicators.RSI(self.extractLabelValues(candle_history, "close"), period)

    def newCandle(self):
        pass

    def ThereIsTransactionOpen(self):
        return (self.client.get_trades()!=[])

    def extractLabelValues(self, data_list, label):
        return [d[label] for d in data_list if label in d]

    def getCurrentCandleClose(self):
        return self.getLastCandleDetails(self.timeframe)[0]['close']
    
    def getCurrentBidPrice(self):
        return self.bid

    def getCurrentCandleOpen(self):
        return self.getNLastCandleDetails(1, self.timeframe)[0]['open']
    
    def getLastTimestamp(self):
        candle_history = self.getNLastCandlesDetails(1, 1)
        timestamp = self.extractLabelValues(candle_history, "timestamp")
        return timestamp[0]

    def getLastCandleClose(self):
        return self.getNLastCandlesDetails(self.timeframe,2)[0]['close']
    
    def openTrade(self, volume=0.1, stop_loss=0):
        self.client.open_trade(MODES.BUY.value, self.symbol, volume, stop_loss)

    def openTrade_stop_loss(self, volume=0.03, stop_loss=0):
        try:
            self.client.open_trade_stop_loss(MODES.BUY.value, self.symbol, volume, float(stop_loss) * PIP_Multiplier[self.symbol])
        except Exception as e:
            self.DEBUG_PRINT("Tranzactia nu a putut fi deschisa: "+ str(self.GetProperties()))

    def closeTrade(self):
        try:
            trades = self.client.update_trades()
            if trades:
                order_id = next(iter(trades))
                self.client.close_trade(order_id)
            else:
                self.DEBUG_PRINT("Nu există tranzacții deschise de închis.")
        except Exception as e:
            self.DEBUG_PRINT(str(e))

    def RetryLogin(self):
        try:
            if self.appRetryConnectCount == 1:
                self.client.retry_login()
                self.appRetryConnectCount = 0
            else:
                self.appRetryConnectCount = self.appRetryConnectCount + 1

        except Exception as e:
            pass
        pass
        
    ###### DO NOT CHANGE ######
    async def __tick(self, timeframe_in_minutes):
        self.DEBUG_PRINT("Thread started.")
        var = True
        while not self.stop_event.is_set():  # Verifică dacă s-a dat semnalul de oprire  
            try:
                self.currentCandle = self.getLastCandleDetails(1)[0]['timestamp']
                if self.currentCandle != self.lastCandle and self.lastCandle != 0:
                    if(self.currentCandle % (self.timeframe * 60) == ((self.timeframe-1)*60)):
                        self.newCandle()
                        self.RetryLogin()
                self.lastCandle = self.currentCandle
                var = True
            except Exception as e:
                self.RetryLogin()
        self.DEBUG_PRINT("Thread stopped.")

##########################################################################################################################################
# Functions below are used for backtest and DEBUG

    def DEBUG_PRINT(self, text):
        if self.BACKTEST == False:
            # Setează fusul orar pentru București
            bucharest_tz = pytz.timezone('Europe/Bucharest')
            timestamp = datetime.now(bucharest_tz)
            formatted_time = timestamp.strftime('%Y-%m-%d %H-%M-%S')

            # Formatează mesajul
            message = f"{formatted_time} DEBUG PRINT: {text}\n"
            # Scrie mesajul în fișier (mod append)
            with open(self.logFile, 'a') as file:
                file.write(message)
                            
        else:
            self.TEST_DEBUG_PRINT(self.time, text)


    def TEST_DEBUG_PRINT(self, time, text):
        reset_color = "\033[0m"  # Codul ANSI pentru resetarea culorii
        print(f"{time} DEBUG PRINT: {text}{reset_color}")

    def TEST_CURRENT_TIME_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length)
        timestamps = self.extractLabelValues(candle_history, "timestamp")
        gmt_plus_2 = timezone(timedelta(hours=2))
        formatted_times = [
            datetime.fromtimestamp(ts, gmt_plus_2).strftime('%Y-%m-%d %H:%M:%S')
            for ts in timestamps
        ]
        return formatted_times
    
    def TEST_CURRENT_TIMESTAMP_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length)
        timestamps = self.extractLabelValues(candle_history, "timestamp")
        return timestamps
    
    def TEST_CURRENT_CLOSE_LAST_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length)
        return self.extractLabelValues(candle_history, "close")
    
    def TEST_LAST_CLOSE_LAST_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length+1)
        arr = self.extractLabelValues(candle_history, "close")
        arr.pop()
        return arr
    

    def TEST_CURRENT_LOW_LAST_N_VALUES(self, length):
        candle_history = self.getNLastCandlesDetails(self.timeframe, length)
        return self.extractLabelValues(candle_history, "low")


    def TEST_EMA_LAST_N_VALUES(self, length, ema_period):
        close_array = self.TEST_CURRENT_CLOSE_LAST_N_VALUES(length + 3*ema_period)
        arr = []
        for i in range(length):
            close_array_i = close_array[i+1:3*ema_period+i+1]
            ema = Indicators.EMA(close_array_i, ema_period)
            arr.append(round(float(ema), 5))
        return arr

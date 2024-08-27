import threading
import datetime
import asyncio
from Strategies import indicators
from enum import Enum
from XTBApi.api import TRANS_TYPES
from XTBApi.api import MODES

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


class Strategy:
    def __init__(self, client, symbol, timeframe, volume=0.1):
        self.client = client
        self.symbol = symbol
        self.timeframe = timeframe
        self.volume = volume
        self.thread = None
        self.process = None
        self.lastCandle = None
        self.currentCandle = None
        self.stop_event = threading.Event()
        self.openTradeCount = 0
    
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
    
    def getNLastCandlesDetails(self, timeframe_in_minutes, number_of_candles):
        candle_history = []
        candle_history = self.client.get_lastn_candle_history(self.symbol, timeframe_in_minutes * 60, number_of_candles)
        return candle_history
    
    def calculateEMA(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return indicators.EMA(self.extractLabelValues(candle_history, "close"), period)
    
    def calculateSMA(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return indicators.SMA(self.extractLabelValues(candle_history, "close"), period)

    def calculateRSI(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return indicators.RSI(self.extractLabelValues(candle_history, "close"), period)

    def tick(self):
        candle_history = self.getNLastCandlesDetails(Timeframe.M15.value, 10)
        # print (self.extractLabelValues(candle_history, "close"))
        return 0

    def newCandle(self):
        self.DEBUG_PRINT("\033[33mEMA: " + str(self.calculateEMA(60, Timeframe.M15.value)))
        self.DEBUG_PRINT("\033[34mSMA: " + str(self.calculateSMA(60, Timeframe.M15.value)))
        self.DEBUG_PRINT("\033[35mRSI: " + str(self.calculateRSI(60, Timeframe.M15.value)))

    def extractLabelValues(self, data_list, label):
        return [d[label] for d in data_list if label in d]

    
    def openTrade(self):
        self.client.open_trade(MODES.BUY.value, self.symbol, self.volume)

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

    async def __tick(self, timeframe_in_minutes):
        while not self.stop_event.is_set():  # Verifică dacă s-a dat semnalul de oprire
            self.tick()
            self.currentCandle = self.getLastCandleDetails(timeframe_in_minutes)
            
            if self.currentCandle != self.lastCandle:
                if self.lastCandle != None:
                    self.newCandle()
                self.lastCandle = self.currentCandle
                
            await asyncio.sleep(1)  # Așteaptă 1 secundă
        self.DEBUG_PRINT("\033[33mThread stopped.")

    def DEBUG_PRINT(self, text):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reset_color = "\033[0m"  # Codul ANSI pentru resetarea culorii
        print(f"{current_time} DualEMAStrategy - DEBUG PRINT: {text}{reset_color}")
import threading
import datetime
import asyncio
from strategies import Indicators
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
        self.appRetryConnectCount = 0
    
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
        candle_history = self.getNLastCandlesDetails(timeframe, 3 * period)
        return Indicators.EMA(self.extractLabelValues(candle_history, "close"), period)
    
    def calculateSMA(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return Indicators.SMA(self.extractLabelValues(candle_history, "close"), period)

    def calculateRSI(self, period, timeframe):
        candle_history = self.getNLastCandlesDetails(timeframe, period)
        return Indicators.RSI(self.extractLabelValues(candle_history, "close"), period)

    def tick(self):
        #self.DEBUG_PRINT("Close price: " + str(self.getCurrentCandleClose()))
        pass

    def newCandle(self):
        # self.DEBUG_PRINT("\033[33mNew candle")
        pass

    def extractLabelValues(self, data_list, label):
        return [d[label] for d in data_list if label in d]

    def getCurrentCandleClose(self):
        return self.getLastCandleDetails(self.timeframe)[0]['close']
    
    def getCurrentCandleOpen(self):
        return self.getLastCandleDetails(self.timeframe)[0]['open']
    
    def getLastCandleClose(self):
        return self.getNLastCandlesDetails(self.timeframe,2)[0]['close']
    
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

    def RetryLogin(self):
        try:
            self.client.retry_login()
        except Exception as e:
            self.login_window.ShowError("Login Failed", f"Login failed: {str(e)}")
        pass

    async def __tick(self, timeframe_in_minutes):
        self.DEBUG_PRINT("\033[33mThread started.")
        while not self.stop_event.is_set():  # Verifică dacă s-a dat semnalul de oprire
            self.tick()
            self.currentCandle = self.getLastCandleDetails(timeframe_in_minutes)
            
            if self.currentCandle != self.lastCandle:
                if self.lastCandle != None:
                    self.newCandle()

                    if self.appRetryConnectCount == 10:
                        self.RetryLogin()
                        self.appRetryConnectCount = 0
                    else:
                        self.appRetryConnectCount = self.appRetryConnectCount + 1

                    
                    # self.DEBUG_PRINT("\033[33mNew candle.")
                self.lastCandle = self.currentCandle
                
            await asyncio.sleep(1)  # Așteaptă 1 secundă
        self.DEBUG_PRINT("\033[33mThread stopped.")

    def DEBUG_PRINT(self, text):
        # Obține timpul curent și scade un minut
        current_time = datetime.datetime.now() - datetime.timedelta(minutes=0)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        reset_color = "\033[0m"  # Codul ANSI pentru resetarea culorii
        print(f"{formatted_time} DEBUG PRINT: {text}{reset_color}")
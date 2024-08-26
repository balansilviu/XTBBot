import threading
import time
import datetime
from XTBApi.api import Client, PERIOD
from multiprocessing import Process
import asyncio

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
    
    def run_strategy(self):
        asyncio.run(self.callback(1))

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
    
    async def callback(self, timeframe_in_minutes):
        while not self.stop_event.is_set():  # Verifică dacă s-a dat semnalul de oprire
            self.currentCandle = self.getLastCandleDetails(timeframe_in_minutes)
            
            if self.currentCandle != self.lastCandle:
                if self.lastCandle != None:
                    self.DEBUG_PRINT("\033[33mNew candle")
                self.lastCandle = self.currentCandle
                
            await asyncio.sleep(1)  # Așteaptă 1 secundă
        self.DEBUG_PRINT("\033[33mThread stopped.")

    def DEBUG_PRINT(self, text):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reset_color = "\033[0m"  # Codul ANSI pentru resetarea culorii
        print(f"{current_time} DualEMAStrategy - DEBUG PRINT: {text}{reset_color}")
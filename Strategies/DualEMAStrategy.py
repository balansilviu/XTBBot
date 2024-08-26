import time
from datetime import datetime
from XTBApi.api import Client, PERIOD
from multiprocessing import Process

class DualEMAStrategy:
    def __init__(self, symbol, timeframe, volume=0.1):
        self.symbol = symbol
        self.timeframe = timeframe
        self.volume = volume
        self.client = Client()
        self.process = None
    
    def fetch_data(self, number_of_candles=10):
        """Fetch the latest market data and print it"""
        candles = self.client.get_lastn_candle_history(self.symbol, self.timeframe * 60, number_of_candles)
        print("Fetched Data:")
        for candle in candles:
            self.DEBUG_PRINT(candle)
        return candles
    
    def _run_strategy(self):
        """Internal method to run the strategy logic"""
        while True:
            self.fetch_data()
            time.sleep(60)  # Așteaptă un minut înainte de următoarea iterație

    def run(self):
        """Run the trading strategy in a separate process"""
        self.process = Process(target=self._run_strategy)
        self.process.start()

    def stop(self):
        """Stop the trading strategy process"""
        if self.process is not None:
            self.process.terminate()
            self.process.join()
            self.process = None

    def DEBUG_PRINT(text):
        print("DualEMAStrategy - DEBUG PRINT:", text)
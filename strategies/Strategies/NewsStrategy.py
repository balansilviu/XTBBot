import asyncio
from datetime import datetime, timezone, timedelta
from strategies.Strategy import Strategy
from ta.trend import EMAIndicator
import ta
import pandas as pd
from enum import Enum
import time
from strategies.Strategy import MODES

class NewsStrategy(Strategy):
    inTrade = False
    lowestEma = 0
    highestEma = 0
    profit = 0
    queue_properties = False
    saved_properties = None
    tradeAllowed = True
    
    def __init__(self, client, symbol, hour=15, minute=30):
        super().__init__(client, symbol)
        self.hour = hour
        self.minute = minute
        self.currentLot = self.volume

    def GetProperties(self):
        baseProperties = super().GetProperties()
        derivedProperties = {
            "Hour": self.hour,
            "Minute": self.minute
        }
        return {**baseProperties, **derivedProperties}
    
    def SetProperties(self, **kwargs):
        super().SetProperties(**kwargs)
        self.maximumLot = 4 * self.volume
        if "Hour" in kwargs:
            self.hour = int(kwargs["Hour"])
        if "Minute" in kwargs:
            self.minute = int(kwargs["Minute"])
    
    def timeUpdate(self):
        if datetime.now().hour == self.hour and datetime.now().minute == (self.minute-1) and datetime.now().second >= 56 and not self.inTrade:
            self.DEBUG_PRINT_CONSOLE("Trades opened")
            self.openTrade_stop_loss(MODES.BUY.value, self.volume, 5.9)
            self.openTrade_stop_loss(MODES.SELL.value, self.volume, 5.9)
            self.inTrade = True
        
        if datetime.now().hour == self.hour and datetime.now().minute == (self.minute+self.timeframe) and datetime.now().second == 0:
            self.DEBUG_PRINT_CONSOLE("Trades closed")
            self.closeAllTrades()
            self.inTrade = False


    def executeStrategy(self):
        self.timeUpdate()

    

    def newCandle(self):  
        super().newCandle()
        self.executeStrategy() 

    async def _tick(self, timeframe_in_minutes):
        while not self.stop_event.is_set():  # Verifică dacă s-a dat semnalul de oprire  
            self.executeStrategy()
            await asyncio.sleep(1)



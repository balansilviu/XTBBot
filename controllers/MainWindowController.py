from views.MainWindow import MainWindow
from models.AppManager import AppManager
from strategies.Strategy import Strategy
from strategies.Strategies.DualEMAStrategy import DualEMAStrategy
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

class MainWindowController:
    def __init__(self, client, all_symbols):
        self.client = client
        self.all_symbols = all_symbols
        self.main_window = None
        self.appManager = AppManager()

    def CreateMainWindow(self):
        self.main_window = MainWindow(self.OnClose, self.all_symbols, self.AddStrategyToTable, self.RemoveSelectedStrategy)
        self.main_window.Show()

    def AddStrategyToTable(self, strategy, chart, timeframe, strategy_table):
        if strategy_table:
            strategy_table.insert("", "end", values=(strategy, chart, timeframe))
            
            # Update strategies vector and start the strategy

            class_instance = globals()[strategy]

            new_strategy = class_instance(self.client, chart, Timeframe[timeframe].value)
            self.appManager.strategyManager.AddStrategy(new_strategy)
            
            # Update table

        
            strategy_table.selection_set(strategy_table.get_children()[0])
            strategy_table.focus(strategy_table.get_children()[0])

    def RemoveSelectedStrategy(self, strategy_table):
        selected_item = strategy_table.selection()
        if selected_item:
            index = strategy_table.index(selected_item)
            self.appManager.strategyManager.DeleteStrategy(index)
            
            strategy_table.delete(selected_item)

            if strategy_table.get_children():
                first_item = strategy_table.get_children()[0]
                strategy_table.selection_set(first_item)
                strategy_table.focus(first_item)

    def OnClose(self):
        self.appManager.strategyManager.StopAllStrategies()
        self.main_window.Close()

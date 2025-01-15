from views.MainWindow import MainWindow
from models.AppManager import AppManager
from strategies.Strategy import Strategy
from strategies.Strategies.DualEMA_Martingale_Tester import DualEMA_Martingale_Tester
from enum import Enum

import os
import glob
import inspect
import importlib

# Specifică folderul unde se află modulele
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Un nivel mai sus
strategies_dir = os.path.join(base_dir, "strategies/Strategies")

# Găsește toate fișierele Python din folder
modules = glob.glob(os.path.join(strategies_dir, "*.py"))

# Dictionar temporar pentru stocarea claselor
classes_to_add = {}

for module_path in modules:
    # Exclude `__init__.py` și alte fișiere care nu sunt module Python valide
    if not module_path.endswith("__init__.py") and module_path.endswith(".py"):
        module_name = f"strategies.Strategies.{os.path.basename(module_path)[:-3]}"
        
        # Importă modulul
        module = importlib.import_module(module_name)
        
        # Găsește toate clasele definite în modul
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module_name:
                # Adaugă clasa într-un dicționar temporar
                classes_to_add[name] = obj

# Adaugă toate clasele din dicționar la `globals()` după încheierea iterației
globals().update(classes_to_add)

# Testare: clasele sunt acum disponibile în `globals()`
for strategy_name in classes_to_add:
    print(f"Loaded class: {strategy_name}")

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
        self.main_window = MainWindow(self.OnClose, self.all_symbols, self.AddStrategyToTable, self.RemoveSelectedStrategy, self.Test1ButtonAction, self.Test2ButtonAction)
        self.main_window.Show()

    def AddStrategyToTable(self, strategy, chart, timeframe, stop_loss, strategy_table):
        if strategy_table:
            strategy_table.insert("", "end", values=(strategy, chart, timeframe))
            
            # Update strategies vector and start the strategy

            class_instance = globals()[strategy]

            new_strategy = class_instance(self.client, chart, Timeframe[timeframe].value, float(stop_loss))
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

    def Test1ButtonAction(self, chart, timeframe):
        strategy = Strategy(self.client, chart, timeframe, volume=0.1)
        strategy.openTrade_stop_loss(0.5, 2)

    def Test2ButtonAction(self, chart, timeframe):
        # print(self.client.get_last_closed_trade())

        strategy = DualEMA_Martingale_Tester(self.client, chart, Timeframe[timeframe].value, volume=0.1)

        strategy.Test()
        
        pass

    def OnClose(self):
        self.appManager.strategyManager.StopAllStrategies()
        self.main_window.Close()

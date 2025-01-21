from views.MainWindow import MainWindow
from models.AppManager import AppManager
from strategies.Strategy import Strategy
from strategies.Strategies.DualEMA_Martingale_Tester import DualEMA_Martingale_Tester
from enum import Enum
from views.PropertiesWindow import show_properties_window
from datetime import datetime
import pytz

import os
import glob
import inspect
import importlib
import re

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
    def __init__(self, client, all_symbols, appManager):
        self.client = client
        self.all_symbols = all_symbols
        self.main_window = None
        self.appManager = appManager

    def CreateMainWindow(self):
        self.main_window = MainWindow(self.appManager, self.OnClose, self.all_symbols, self.AddStrategyToTable, self.RemoveSelectedStrategy, self.Test1ButtonAction, self.Test2ButtonAction)
        self.main_window.Show()

    def AddStrategyToTable(self, strategy, chart, timeframe, strategy_table):
        if strategy_table:
            strategy_table.insert("", "end", values=(strategy, chart, timeframe))
            
            # Update strategies vector and start the strategy
            print(strategy)
            class_instance = globals()[strategy]

            new_strategy = class_instance(self.client, chart)

            # Obține valorile din fereastra de proprietăți
            values = show_properties_window(new_strategy.GetProperties())
            if values is not None:
                new_strategy.SetProperties(**values)

            file_name = self.CreateLogFile(strategy)
            new_strategy.SetLogFile(file_name)
            self.appManager.strategyManager.AddStrategy(new_strategy)
            
            # Update table
            strategy_table.selection_set(strategy_table.get_children()[0])
            strategy_table.focus(strategy_table.get_children()[0])

    def CreateLogFile(self, strategy_name):
        # Obține timpul actual în fusul orar al Bucureștiului și îl formatează
        bucharest_tz = pytz.timezone('Europe/Bucharest')
        timestamp = datetime.now(bucharest_tz)
        formatted_time = timestamp.strftime('%Y-%m-%d %H-%M-%S')  # Înlocuiește ":" cu "-" direct în format

        # Creează folderul logs dacă nu există
        os.makedirs("logs", exist_ok=True)

        # Creează numele fișierului fără extensie
        file_name = f"logs/{formatted_time}_{strategy_name}"

        # Creează fișierul gol
        open(file_name, 'w').close()

        # Formatează mesajul
        message = f"Username: {self.appManager.username}\n"
        # Scrie mesajul în fișier (mod append)
        with open(file_name, 'a') as file:
            file.write(message)

         # Formatează mesajul
        message = f"Strategy: {strategy_name}\n"
        # Scrie mesajul în fișier (mod append)
        with open(file_name, 'a') as file:
            file.write(message)

        return file_name

    def RemoveSelectedStrategy(self, strategy_table):
        selected_item = strategy_table.selection()
        if selected_item:
            index = strategy_table.index(selected_item)
            self.RenameLogFile(self.appManager.strategyManager.strategies[index])
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

        strategy = DualEMA_Martingale_Tester(self.client, chart, Timeframe[timeframe].value, volume=0.5)

        strategy.Test()
        
        pass

    def RenameLogFile(self, strategy):
        filename = strategy.GetLogFile()
         # Setează fusul orar pentru București
        bucharest_tz = pytz.timezone('Europe/Bucharest')
        timestamp = datetime.now(bucharest_tz)
        formatted_time = timestamp.strftime('%Y-%m-%d %H-%M-%S')
        
        date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}'
        matches = re.findall(date_pattern, filename)
        if(len(matches) == 1):
            part1, part2 = filename.split("_", 1)
            new_filename = f"{part1}_to_{formatted_time}_{part2}"
            os.rename(filename, new_filename)
            strategy.SetLogFile(new_filename)
        elif (len(matches) == 2):
            parts = filename.split("_")
            parts[2] = formatted_time
            new_filename = "_".join(parts)
            os.rename(filename, new_filename)
            strategy.SetLogFile(new_filename)
        else:
            print("Eroare la redenumirea fisierului de log")


    def OnClose(self):

        for strategy in self.appManager.strategyManager.strategies:
            self.RenameLogFile(strategy)

        self.appManager.strategyManager.StopAllStrategies()
        self.main_window.Close()

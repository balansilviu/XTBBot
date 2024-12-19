from views.main_window import MainWindow

class MainWindowController:
    def __init__(self, client, all_symbols):
        self.client = client
        self.all_symbols = all_symbols
        self.strategies = []
        self.main_window = None

    def CreateMainWindow(self):
        self.main_window = MainWindow(self.OnClose, self.all_symbols, self.AddStrategyToTable, self.RemoveSelectedStrategy)
        self.main_window.Show()

    def AddStrategyToTable(self, strategy, chart, timeframe, strategy_table):
        if strategy_table:
            strategy_table.insert("", "end", values=(strategy, chart, timeframe))
            # new_strategy = ClientManager().CreateStrategy(self.client, chart, timeframe)
            # self.strategies.append(new_strategy)
            strategy_table.selection_set(strategy_table.get_children()[0])
            strategy_table.focus(strategy_table.get_children()[0])
            # self.strategies[-1].Run()

    def RemoveSelectedStrategy(self, strategy_table):
        selected_item = strategy_table.selection()
        if selected_item:
            index = strategy_table.index(selected_item)
            self.strategies[index].Stop()
            self.strategies.pop(index)
            strategy_table.delete(selected_item)

            if strategy_table.get_children():
                first_item = strategy_table.get_children()[0]
                strategy_table.selection_set(first_item)
                strategy_table.focus(first_item)

    def OnClose(self):
        for strategy in self.strategies:
            strategy.Stop()
        self.main_window.Close()

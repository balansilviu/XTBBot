import os
import customtkinter as ctk
from tkinter import StringVar, Listbox, END, ttk

import os
import glob
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
strategies_dir = os.path.join(base_dir, "strategies/Strategies")
modules = glob.glob(os.path.join(strategies_dir, "*.py"))
__all__ = [os.path.basename(f)[:-3] for f in modules if f.endswith(".py") and f != "__init__.py"]

for module in __all__:
    __import__(f"strategies.Strategies.{module}")

class MainWindow:
    def __init__(self, on_close, all_symbols, add_strategy_to_table, remove_selected_strategy):
        self.on_close = on_close
        self.all_symbols = all_symbols
        self.add_strategy_to_table = add_strategy_to_table
        self.remove_selected_strategy = remove_selected_strategy
        self.chart_entry = None
        self.strategy_table = None

    def Show(self):
        self.window = ctk.CTk()
        self.window.title("Trading Bot Interface")
        self.window.geometry("600x750")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.CreateStrategyFrame(self.window)
        self.window.mainloop()

    def CreateStrategyFrame(self, trading_bot_window):
        strategy_frame = ctk.CTkFrame(trading_bot_window)
        strategy_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(strategy_frame, text="Configure Your Strategies", font=("Arial", 20)).pack(pady=10)

        strategy_var = self.CreateStrategySelection(strategy_frame)
        chart_var, self.chart_entry = self.CreateInstrumentSelection(strategy_frame)
        timeframe_var = self.CreateTimeframeSelection(strategy_frame, strategy_var, chart_var)
        self.strategy_table = self.CreateStrategyTable(strategy_frame)

        ctk.CTkButton(strategy_frame, text="Add Strategy", command=lambda: self.add_strategy_to_table(strategy_var.get(), chart_var.get(), timeframe_var.get(), self.strategy_table)).pack(pady=10, padx=10, fill="x")
        self.CreateRemoveButton(strategy_frame)

    def CreateStrategySelection(self, strategy_frame):
        ctk.CTkLabel(strategy_frame, text="Select Strategy:").pack(anchor="w", padx=10)
        strategies = [f[:-3] for f in os.listdir("strategies/Strategies") if f.endswith(".py")]
        default_strategy = strategies[0] if strategies else "Select Strategy"
        strategy_var = StringVar(value=default_strategy)
        ctk.CTkOptionMenu(strategy_frame, variable=strategy_var, values=strategies).pack(pady=5, padx=10, fill="x")
        return strategy_var

    def CreateInstrumentSelection(self, strategy_frame):
        instruments = [symbol_info['symbol'] for symbol_info in self.all_symbols]
        ctk.CTkLabel(strategy_frame, text="Select Instrument:").pack(anchor="w", padx=10)
        chart_var = StringVar(value="EURUSD")
        self.chart_entry = ctk.CTkEntry(strategy_frame, textvariable=chart_var)
        self.chart_entry.pack(pady=5, padx=10, fill="x")
        self.CreateInstrumentListbox(strategy_frame, chart_var, instruments)
        return chart_var, self.chart_entry

    def CreateInstrumentListbox(self, strategy_frame, chart_var, instruments):
        listbox_bg_color = "gray20" if ctk.get_appearance_mode() == "Dark" else "white"
        listbox_fg_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        chart_listbox = Listbox(strategy_frame, height=4, bg=listbox_bg_color, fg=listbox_fg_color)
        chart_listbox.pack(pady=5, padx=10, fill="x")

        def update_listbox(*args):
            search_term = chart_var.get().upper()
            chart_listbox.delete(0, END)
            for instrument in instruments:
                if search_term in instrument:
                    chart_listbox.insert(END, instrument)

        def on_listbox_select(event):
            try:
                selection = chart_listbox.curselection()
                if selection:
                    selected_instrument = chart_listbox.get(selection[0])
                    chart_var.set(selected_instrument)
            except IndexError:
                pass

        chart_var.trace("w", update_listbox)
        chart_listbox.bind("<<ListboxSelect>>", on_listbox_select)
        self.chart_entry.bind("<FocusIn>", lambda event: chart_listbox.pack(pady=5, padx=10, fill="x"))

    def CreateTimeframeSelection(self, strategy_frame, strategy_var, chart_var):
        ctk.CTkLabel(strategy_frame, text="Select Timeframe:").pack(anchor="w", padx=10)
        timeframe_var = StringVar(value="M1")
        ctk.CTkOptionMenu(strategy_frame, variable=timeframe_var, values=["M1", "M5", "M30", "H1", "H4", "D1", "W1", "MN"]).pack(pady=5, padx=10, fill="x")
        return timeframe_var

    def CreateStrategyTable(self, strategy_frame):
        columns = ('Strategy', 'Instrument', 'Timeframe')
        strategy_table = ttk.Treeview(strategy_frame, columns=columns, show='headings')
        strategy_table.heading('Strategy', text='Strategy')
        strategy_table.heading('Instrument', text='Instrument')
        strategy_table.heading('Timeframe', text='Timeframe')
        strategy_table.pack(pady=20, padx=10, fill="both", expand=True)
        return strategy_table

    def CreateRemoveButton(self, strategy_frame):
        ctk.CTkButton(strategy_frame, text="Remove Selected Strategy", command=lambda: self.remove_selected_strategy(self.strategy_table)).pack(pady=10, padx=10, fill="x")

    def Close(self):
        self.window.destroy()

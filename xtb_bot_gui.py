import customtkinter as ctk
from tkinter import ttk, StringVar, Listbox, END
import shelve
from XTBApi.api import Client

client = Client()
all_symbols = []
chart_entry = []

def main():
    configureApp()
    createLoginWindow()
    app.mainloop()

# Function to configure the app settings
def configureApp():
    ctk.set_appearance_mode("Dark")  # Set to Dark Mode
    ctk.set_default_color_theme("dark-blue")  # Choose the color theme

# Function to show a custom error window
def showCustomError(title, message):
    error_window = ctk.CTkToplevel()  # Create a new modal window
    error_window.title(title)
    error_window.geometry("400x150")  # Set window size

    # Add a label to display the error message
    label = ctk.CTkLabel(error_window, text=message)
    label.pack(pady=20)

    # Add an "OK" button to close the window
    ok_button = ctk.CTkButton(error_window, text="OK", command=error_window.destroy)
    ok_button.pack(pady=10)

# Function to create the login window
def createLoginWindow():
    global app, username_entry, password_entry, remember_me_var
    app = ctk.CTk()
    app.title("Login Page")
    app.geometry("300x450")
    app.resizable(False, False)

    login_frame = ctk.CTkFrame(app)
    login_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Add an icon or avatar at the top (for demonstration, using text)
    avatar_label = ctk.CTkLabel(login_frame, text="⬤", font=("Arial", 50))
    avatar_label.pack(pady=20)

    # Login title
    login_label = ctk.CTkLabel(login_frame, text="Login", font=("Arial", 20))
    login_label.pack(pady=10)

    # Username entry with icon
    username_entry = ctk.CTkEntry(login_frame, placeholder_text="Username")
    username_entry.pack(pady=10, padx=10)

    # Password entry with icon
    password_entry = ctk.CTkEntry(login_frame, placeholder_text="Password", show="*")
    password_entry.pack(pady=10, padx=10)

    # Show password button
    show_password_button = ctk.CTkButton(login_frame, text="👁", width=30, command=togglePasswordVisibility)
    show_password_button.place(relx=0.85, rely=0.45)

    # Remember me checkbox
    remember_me_var = ctk.BooleanVar()
    remember_me_checkbox = ctk.CTkCheckBox(login_frame, text="Remember me", variable=remember_me_var)
    remember_me_checkbox.pack(pady=5, anchor="w", padx=10)

    # Forgot password link (simulated with a button)
    forgot_password_button = ctk.CTkButton(login_frame, text="Forgot password?", fg_color="transparent", hover_color="gray", text_color="blue", width=120)
    forgot_password_button.pack(anchor="e", padx=10)

    # Login button
    login_button = ctk.CTkButton(login_frame, text="LOGIN", command=login)
    login_button.pack(pady=20, padx=10, fill="x")

    # Bind the Enter key to the login action
    app.bind('<Return>', lambda event: login())

    # Load saved credentials if available
    loadSavedCredentials()

# Function to toggle password visibility
def togglePasswordVisibility():
    if password_entry.cget("show") == "*":
        password_entry.configure(show="")
    else:
        password_entry.configure(show="*")

# Function to handle login action
def login():
    global client, all_symbols

    username = username_entry.get()
    password = password_entry.get()

    try:
        response = client.login(username, password)

        if response is None:
            if remember_me_var.get():
                saveCredentials(username, password)

            all_symbols = client.get_all_symbols()
            app.destroy()  # Close the login window after successful login
            openTradingBotInterface()  # Open the trading bot interface
        else:
            showCustomError("Login Failed", "Invalid username or password")
    except Exception as e:
        showCustomError("Login Failed", f"Login failed: {str(e)}")

# Function to save credentials
def saveCredentials(username, password):
    with shelve.open('login_data') as login_data:
        login_data['username'] = username
        login_data['password'] = password

# Function to load saved credentials
def loadSavedCredentials():
    with shelve.open('login_data') as login_data:
        username = login_data.get('username')
        password = login_data.get('password')
        if username and password:
            username_entry.insert(0, username)
            password_entry.insert(0, password)
            remember_me_var.set(True)

# Function to open the trading bot interface
def openTradingBotInterface():
    trading_bot_window = ctk.CTk()
    trading_bot_window.title("Trading Bot Interface")
    trading_bot_window.geometry("600x750")

    createStrategyFrame(trading_bot_window)

    trading_bot_window.mainloop()

# Function to create strategy frame and its elements
def createStrategyFrame(trading_bot_window):
    global chart_entry

    strategy_frame = ctk.CTkFrame(trading_bot_window)
    strategy_frame.pack(pady=20, padx=20, fill="both", expand=True)

    strategy_label = ctk.CTkLabel(strategy_frame, text="Configure Your Strategies", font=("Arial", 20))
    strategy_label.pack(pady=10)

    strategy_var = createStrategySelection(strategy_frame)
    chart_var, chart_entry = createInstrumentSelection(strategy_frame)
    timeframe_var = createTimeframeSelection(strategy_frame, strategy_var, chart_var, chart_entry)
    strategy_table = createStrategyTable(strategy_frame)  # Create the strategy table and capture it

    add_button = ctk.CTkButton(strategy_frame, text="Add Strategy", command=lambda: addStrategyToTable(strategy_var.get(), chart_var.get(), timeframe_var.get(), strategy_table))
    add_button.pack(pady=10, padx=10, fill="x")

    createRemoveButton(strategy_frame, strategy_table)

# Function to create strategy selection elements
def createStrategySelection(strategy_frame):
    strategy_var = ctk.StringVar(value="Moving Average")
    strategy_label = ctk.CTkLabel(strategy_frame, text="Select Strategy:")
    strategy_label.pack(anchor="w", padx=10)

    strategy_menu = ctk.CTkOptionMenu(strategy_frame, variable=strategy_var, values=["Moving Average", "RSI", "MACD", "Bollinger Bands"])
    strategy_menu.pack(pady=5, padx=10, fill="x")

    return strategy_var

# Function to create instrument selection elements
def createInstrumentSelection(strategy_frame):
    global all_symbols
    global chart_entry
    instruments = [symbol_info['symbol'] for symbol_info in all_symbols]

    chart_label = ctk.CTkLabel(strategy_frame, text="Select Instrument:")
    chart_label.pack(anchor="w", padx=10)

    chart_var = StringVar()
    chart_entry = ctk.CTkEntry(strategy_frame, textvariable=chart_var)
    chart_entry.pack(pady=5, padx=10, fill="x")

    createInstrumentListbox(strategy_frame, chart_var, instruments)

    return chart_var, chart_entry

# Function to create the instrument listbox
def createInstrumentListbox(strategy_frame, chart_var, instruments):
    # Determine background color based on current theme
    bg_color = ctk.get_appearance_mode()
    listbox_bg_color = "gray20" if bg_color == "Dark" else "white"
    listbox_fg_color = "white" if bg_color == "Dark" else "black"

    # Listbox for showing matching instruments
    chart_listbox = Listbox(strategy_frame, height=4, bg=listbox_bg_color, fg=listbox_fg_color)
    chart_listbox.pack(pady=5, padx=10, fill="x")

    def updateListbox(*args):
        search_term = chart_var.get().upper()
        chart_listbox.delete(0, END)
        for instrument in instruments:
            if search_term in instrument:
                chart_listbox.insert(END, instrument)

    def populateListbox():
        chart_listbox.delete(0, END)
        for instrument in instruments:
            chart_listbox.insert(END, instrument)

    chart_var.trace("w", updateListbox)

    def onListboxSelect(event):
        try:
            selection = chart_listbox.curselection()
            if selection:  # Verifică dacă există o selecție
                selected_instrument = chart_listbox.get(selection[0])  # Ia primul element din selecție
                chart_var.set(selected_instrument)
        except IndexError:
            pass

    chart_listbox.bind("<<ListboxSelect>>", onListboxSelect)
    populateListbox()

    chart_entry.bind("<FocusIn>", lambda event: chart_listbox.pack(pady=5, padx=10, fill="x"))

# Function to create timeframe selection elements
def createTimeframeSelection(strategy_frame, strategy_var, chart_var, chart_entry):
    timeframe_var = ctk.StringVar(value="1 Hour")
    timeframe_label = ctk.CTkLabel(strategy_frame, text="Select Timeframe:")
    timeframe_label.pack(anchor="w", padx=10)

    timeframe_menu = ctk.CTkOptionMenu(strategy_frame, variable=timeframe_var, values=["1 Minute", "5 Minutes", "15 Minutes", "1 Hour", "4 Hours", "1 Day"])
    timeframe_menu.pack(pady=5, padx=10, fill="x")

    return timeframe_var

# Function to create the strategy table
def createStrategyTable(strategy_frame):
    columns = ('Strategy', 'Instrument', 'Timeframe')
    strategy_table = ttk.Treeview(strategy_frame, columns=columns, show='headings')

    strategy_table.heading('Strategy', text='Strategy')
    strategy_table.heading('Instrument', text='Instrument')
    strategy_table.heading('Timeframe', text='Timeframe')

    strategy_table.pack(pady=20, padx=10, fill="both", expand=True)

    return strategy_table  # Return the strategy_table instance

# Function to add strategy to the table
def addStrategyToTable(strategy, chart, timeframe, strategy_table):
    if strategy_table:
        strategy_table.insert("", "end", values=(strategy, chart, timeframe))

# Function to create remove button
def createRemoveButton(strategy_frame, strategy_table):
    remove_button = ctk.CTkButton(strategy_frame, text="Remove Selected Strategy", command=lambda: removeSelectedStrategy(strategy_table))
    remove_button.pack(pady=10, padx=10, fill="x")

# Function to remove the selected strategy
def removeSelectedStrategy(strategy_table):
    selected_item = strategy_table.selection()  # Get selected item
    if selected_item:
        strategy_table.delete(selected_item)  # Remove the selected item

if __name__ == "__main__":
    main()

import shelve

from views.LoginWindow import LoginWindow
from controllers.MainWindowController import MainWindowController

class LoginWindowController:
    def __init__(self, app, appManager):
        self.app = app
        self.appManager = appManager
        self.client = self.appManager.GetClientManager().GetClient()
        self.all_symbols = []
        self.login_window = None

    def CreateLoginWindow(self):
        self.login_window = LoginWindow(self.app, self.OnLogin, self.TogglePasswordVisibility)
        self.login_window.Show()
        self.LoadSavedCredentials()

    def TogglePasswordVisibility(self):
        self.login_window.TogglePasswordVisibility()

    def OnLogin(self):
        username, password, remember_me = self.login_window.GetCredentials()
        self.appManager.username = username
        self.appManager.GetClientManager().username = username
        self.appManager.GetClientManager().password = password

        try:
            response = self.client.login(username, password)
            if response is None:
                if remember_me:
                    self.SaveCredentials(username, password)

                self.all_symbols = self.client.get_all_symbols()
                self.app.destroy()
                self.OpenTradingBotInterface()
            else:
                self.login_window.ShowError("Login Failed", "Invalid username or password")
        except Exception as e:
            if "Handshake status 404 Not Found" in str(e):
                print("Market inchis")
                self.login_window.ShowError("Login Failed", f"Login failed: Mentenanta tehnica")

            else:
                print({str(e)}) 
                self.login_window.ShowError("Login Failed", f"Login failed: {str(e)}")

    

    def SaveCredentials(self, username, password):
        with shelve.open('login_data') as login_data:
            login_data['username'] = username
            login_data['password'] = password

    def LoadSavedCredentials(self):
        with shelve.open('login_data') as login_data:
            username = login_data.get('username')
            password = login_data.get('password')
            if username and password:
                self.login_window.SetCredentials(username, password, True)

    def OpenTradingBotInterface(self):
        main_window_controller = MainWindowController(self.client, self.all_symbols, self.appManager)
        main_window_controller.CreateMainWindow()

import shelve
from models.ClientManager import ClientManager
from views.login_window import LoginWindow
from controllers.main_window_controller import MainWindowController

class LoginWindowController:
    def __init__(self, app):
        self.app = app
        self.client = ClientManager().GetClient()
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
        main_window_controller = MainWindowController(self.client, self.all_symbols)
        main_window_controller.CreateMainWindow()

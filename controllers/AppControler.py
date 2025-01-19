import customtkinter as ctk
from controllers.LoginWindowController import LoginWindowController
from models.AppManager import AppManager

class AppController:

    def __init__(self):
        self.app = ctk.CTk()
        self.appManager = AppManager()

    def ConfigureApp(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

    def RunApp(self):
        self.ConfigureApp()
        login_window_controller = LoginWindowController(self.app, self.appManager)
        login_window_controller.CreateLoginWindow()
        self.app.mainloop()

    def OnAppClose(self):
        self.app.destroy()
        self.app.quit()

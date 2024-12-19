import customtkinter as ctk
from controllers.login_window_controller import LoginWindowController

class AppController:
    def __init__(self):
        self.app = ctk.CTk()

    def ConfigureApp(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

    def RunApp(self):
        self.ConfigureApp()
        login_window_controller = LoginWindowController(self.app)
        login_window_controller.CreateLoginWindow()
        self.app.mainloop()

    def OnAppClose(self):
        self.app.destroy()
        self.app.quit()

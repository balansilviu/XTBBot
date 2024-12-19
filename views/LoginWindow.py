import customtkinter as ctk
from tkinter import BooleanVar

class LoginWindow:
    def __init__(self, app, on_login, toggle_password_visibility):
        self.app = app
        self.on_login = on_login
        self.toggle_password_visibility = toggle_password_visibility
        self.username_entry = None
        self.password_entry = None
        self.remember_me_var = BooleanVar()

    def Show(self):
        self.app.title("Login Page")
        self.app.geometry("300x450")
        self.app.resizable(False, False)
        self.app.protocol("WM_DELETE_WINDOW", self.app.destroy)

        login_frame = ctk.CTkFrame(self.app)
        login_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(login_frame, text="⬤", font=("Arial", 50)).pack(pady=20)
        ctk.CTkLabel(login_frame, text="Login", font=("Arial", 20)).pack(pady=10)

        self.username_entry = ctk.CTkEntry(login_frame, placeholder_text="Username")
        self.username_entry.pack(pady=10, padx=10)

        self.password_entry = ctk.CTkEntry(login_frame, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10, padx=10)

        ctk.CTkButton(login_frame, text="👁", width=30, command=self.toggle_password_visibility).place(relx=0.85, rely=0.45)
        ctk.CTkCheckBox(login_frame, text="Remember me", variable=self.remember_me_var).pack(pady=5, anchor="w", padx=10)

        ctk.CTkButton(login_frame, text="Forgot password?", fg_color="transparent", hover_color="gray", text_color="blue", width=120).pack(anchor="e", padx=10)
        ctk.CTkButton(login_frame, text="LOGIN", command=self.on_login).pack(pady=20, padx=10, fill="x")

        self.app.bind('<Return>', lambda event: self.on_login())

    def GetCredentials(self):
        return self.username_entry.get(), self.password_entry.get(), self.remember_me_var.get()

    def SetCredentials(self, username, password, remember_me):
        self.username_entry.insert(0, username)
        self.password_entry.insert(0, password)
        self.remember_me_var.set(remember_me)

    def TogglePasswordVisibility(self):
        if self.password_entry.cget("show") == "*":
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")

    def ShowError(self, title, message):
        error_window = ctk.CTkToplevel()
        error_window.title(title)
        error_window.geometry("400x150")
        ctk.CTkLabel(error_window, text=message).pack(pady=20)
        ctk.CTkButton(error_window, text="OK", command=error_window.destroy).pack(pady=10)

from controllers.AppControler import AppController
import logging
from strategies.Strategy import Strategy
from views.PropertiesWindow import PropertiesWindow
from PyQt5.QtWidgets import (
    QApplication, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, QWidget
)
import sys

from views.PropertiesWindow import PropertiesWindow


if __name__ == "__main__":
    # app_controller = AppController()
    # app_controller.RunApp()
    
    
    app = QApplication(sys.argv)
    window = PropertiesWindow()
    window.show()
    sys.exit(app.exec_())
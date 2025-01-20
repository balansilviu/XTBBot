from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QMessageBox, QApplication
)
import sys

class PropertiesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Strategy Properties")
        self.setGeometry(100, 100, 400, 350)
        self.result = None  # Atribuim rezultatele aici

        # Crearea TreeWidget-ului
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Property", "Value"])
        self.tree.setColumnWidth(0, 150)

        # Eliminare efecte de selecție și hover doar pentru elementele de tip TreeWidgetItem
        self.tree.setStyleSheet("""
            QTreeWidget::item:selected {
                background: transparent;  /* Elimină fundalul la selectare */
                color: black;  /* Păstrează textul negru */
            }
            QTreeWidget::item:hover {
                background: transparent;  /* Elimină fundalul la hover */
            }
        """)

        # Adăugare proprietăți pentru strategia de trading
        self.add_property("Timeframe", self.create_dropdown([
            "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"
        ]))
        self.ema1_field = self.add_property("EMA 1", "12")
        self.ema2_field = self.add_property("EMA 2", "26")
        self.stop_loss_field = self.add_property("Stop loss", "50")
        self.starting_lots_field = self.add_property("Starting lots", "0.1")

        # Crearea butoanelor OK și Cancel
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.on_ok_pressed)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_pressed)

        # Aplicăm stilul pe butoane
        self.ok_button.setStyleSheet(self.button_style())
        self.cancel_button.setStyleSheet(self.button_style())

        # Layout pentru butoane
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tree)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def add_property(self, prop_name, value):
        """Adaugă o proprietate în TreeWidget."""
        item = QTreeWidgetItem(self.tree)
        item.setText(0, prop_name)
        line_edit = None
        if isinstance(value, QComboBox):
            self.tree.setItemWidget(item, 1, value)
        elif isinstance(value, str):
            line_edit = QLineEdit(value)
            # Eliminăm bordura neagră din QLineEdit
            line_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 2px;
                }
            """)
            self.tree.setItemWidget(item, 1, line_edit)
        return line_edit

    def create_dropdown(self, options):
        """Creează un dropdown box cu opțiuni."""
        combo = QComboBox()
        combo.addItems(options)
        return combo

    def get_values(self):
        """Colectează valorile introduse și returnează un dicționar."""
        try:
            values = {
                "timeframe": self.tree.itemWidget(self.tree.topLevelItem(0), 1).currentText(),
                "ema1": float(self.ema1_field.text()),
                "ema2": float(self.ema2_field.text()),
                "stop_loss": float(self.stop_loss_field.text()),
                "starting_lots": float(self.starting_lots_field.text()),
            }
            return values
        except ValueError:
            QMessageBox.critical(
                self,
                "Invalid Input",
                "One or more properties have invalid values. Please check your input."
            )
            return None

    def on_ok_pressed(self):
        """Salvează valorile și închide fereastra."""
        values = self.get_values()
        if values is not None:
            self.result = values
            self.close()  # Închide fereastra

    def on_cancel_pressed(self):
        """Funcția apelată când se apasă butonul Cancel."""
        self.result = None
        self.close()

    def button_style(self):
        """Stil uniform pentru butoane."""
        return """
            QPushButton {
                background-color: #0078d7;  /* Fundal albastru */
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005a9e;  /* Fundal mai închis la hover */
            }
        """


# Funcție pentru a deschide fereastra și a returna valorile
def show_properties_window():
    app = QApplication(sys.argv)
    window = PropertiesWindow()
    window.show()
    app.exec_()  # Blochează execuția până când fereastra este închisă
    return window.result  # Returnează rezultatele


# Exemplu de utilizare
if __name__ == "__main__":
    values = show_properties_window()
    if values:
        print("Valori introduse:", values)
    else:
        print("Fereastra a fost anulată.")

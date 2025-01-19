from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QMessageBox
)


class PropertiesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Strategy Properties")
        self.setGeometry(100, 100, 400, 350)

        # Crearea TreeWidget-ului
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Property", "Value"])
        self.tree.setColumnWidth(0, 150)  # Lățime fixă pentru prima coloană

        # Eliminare efecte de selecție și hover
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
        self.ema1_field = self.add_property("EMA 1", "12")  # Valoare editabilă implicită
        self.ema2_field = self.add_property("EMA 2", "26")  # Valoare editabilă implicită
        self.stop_loss_field = self.add_property("Stop loss", "50")  # Valoare editabilă implicită
        self.starting_lots_field = self.add_property("Starting lots", "0.1")  # Valoare editabilă implicită

        # Crearea butoanelor OK și Cancel
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.on_ok_pressed)  # Conectare la funcție

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_pressed)  # Conectare la funcție

        # Layout pentru butoane
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # Adaugă spațiu flexibil la stânga
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)  # Adaugă spațiu flexibil la dreapta

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tree)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def add_property(self, prop_name, value):
        """Adaugă o proprietate direct în tree."""
        item = QTreeWidgetItem(self.tree)
        item.setText(0, prop_name)
        line_edit = None
        if isinstance(value, QComboBox):  # Dropdown box
            self.tree.setItemWidget(item, 1, value)
        elif isinstance(value, str):  # Editabil text
            line_edit = QLineEdit(value)
            line_edit.setStyleSheet("border: none; padding: 2px;")  # Elimină chenarul
            self.tree.setItemWidget(item, 1, line_edit)
        return line_edit  # Returnăm QLineEdit pentru validare

    def create_dropdown(self, options):
        """Creează un dropdown box cu opțiuni."""
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet("border: none; padding: 2px;")  # Elimină chenarul
        return combo

    def on_ok_pressed(self):
        """Funcția apelată când se apasă butonul OK."""
        try:
            # Validare fiecare câmp editabil
            ema1 = float(self.ema1_field.text())
            ema2 = float(self.ema2_field.text())
            stop_loss = float(self.stop_loss_field.text())
            starting_lots = float(self.starting_lots_field.text())

            # Dacă toate sunt valide, poți procesa datele aici
            print(f"EMA 1: {ema1}, EMA 2: {ema2}, Stop loss: {stop_loss}, Starting lots: {starting_lots}")

        except ValueError:
            # Afișare mesaj de eroare dacă există un câmp invalid
            QMessageBox.critical(
                self,
                "Invalid Input",
                "One or more properties have invalid values. Please enter numeric values for all editable fields.",
            )

    def on_cancel_pressed(self):
        """Funcția apelată când se apasă butonul Cancel."""
        self.close()

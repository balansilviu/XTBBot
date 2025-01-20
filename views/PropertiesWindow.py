from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QComboBox, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QMessageBox, QApplication
)
from enum import Enum
import sys


class Timeframe(Enum):
    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    D1 = 1440
    W1 = 10080
    MN = 43200


class PropertiesWindow(QWidget):
    def __init__(self, properties):
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

        # Adăugare proprietăți din variabila `properties`
        self.fields = {}
        for key, value in properties.items():
            if key == "Symbol":
                # Adăugăm un QLabel pentru a face câmpul Symbol needitabil
                self.fields[key] = self.add_label_property(key, value)
            elif key == "Timeframe":
                # Adăugăm dropdown pentru Timeframe
                self.fields[key] = self.add_property(key, self.create_dropdown([tf.name for tf in Timeframe], str(value)))
            else:
                # Adăugăm câmp text pentru alte proprietăți
                if isinstance(value, (int, float)):
                    value = str(value)  # Convertim în string pentru afișare în QLineEdit
                self.fields[key] = self.add_property(key, value)

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
        """Adaugă o proprietate editabilă (QLineEdit sau QComboBox) în TreeWidget."""
        item = QTreeWidgetItem(self.tree)
        item.setText(0, prop_name)
        if isinstance(value, QComboBox):
            self.tree.setItemWidget(item, 1, value)
            return value
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

    def add_label_property(self, prop_name, value):
        """Adaugă o proprietate needitabilă (QLabel) în TreeWidget."""
        item = QTreeWidgetItem(self.tree)
        item.setText(0, prop_name)
        label = QLabel(value)
        self.tree.setItemWidget(item, 1, label)
        return label

    def create_dropdown(self, options, default_value):
        """Creează un dropdown box cu opțiuni și selectează valoarea implicită."""
        combo = QComboBox()
        combo.addItems(options)
        if default_value in options:
            combo.setCurrentText(default_value)
        return combo

    def get_values(self):
        """Colectează valorile introduse și returnează un dicționar."""
        try:
            values = {}
            for key, field in self.fields.items():
                if isinstance(field, QComboBox):
                    # Dacă este dropdown, returnăm valoarea selectată
                    selected_name = field.currentText()
                    if key == "Timeframe":
                        values[key] = Timeframe[selected_name].value  # Convertim la valoarea numerică
                elif isinstance(field, QLineEdit):
                    # Dacă este text, returnăm valoarea introdusă
                    text_value = field.text()
                    values[key] = float(text_value) if text_value.replace('.', '', 1).isdigit() else text_value
                elif isinstance(field, QLabel):
                    # Dacă este QLabel, returnăm textul
                    values[key] = field.text()
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
def show_properties_window(properties):
    app = QApplication(sys.argv)
    window = PropertiesWindow(properties)
    window.show()
    app.exec_()  # Blochează execuția până când fereastra este închisă
    return window.result  # Returnează rezultatele
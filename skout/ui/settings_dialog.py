# SPDX-FileCopyrightText: 2026 Loc Huynh <huynhloc.contact@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSlider, QPushButton, QFormLayout
)
from PySide6.QtCore import Qt
from skout.ui.config import Settings, Theme

class SettingsDialog(QDialog):
    """KDE-style configuration dialog for Skout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Skout")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)
        
        # 1. Player Name
        self.edit_name = QLineEdit(Settings.player_name)
        self.edit_name.setPlaceholderText("Enter your name...")
        form.addRow("Player Name:", self.edit_name)
        
        # 2. Bot Delay (Speed)
        self.slider_delay = QSlider(Qt.Horizontal)
        self.slider_delay.setRange(200, 3000)
        self.slider_delay.setSingleStep(100)
        self.slider_delay.setValue(Settings.bot_delay)
        
        self.lbl_delay_val = QLabel(f"{Settings.bot_delay}ms")
        self.slider_delay.valueChanged.connect(lambda v: self.lbl_delay_val.setText(f"{v}ms"))
        
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(self.slider_delay)
        delay_layout.addWidget(self.lbl_delay_val)
        form.addRow("Bot Speed:", delay_layout)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.save_and_close)
        btn_ok.setDefault(True)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def save_and_close(self):
        """Persists choices to QSettings."""
        Settings.player_name = self.edit_name.text() or "You"
        Settings.bot_delay = self.slider_delay.value()
        self.accept()

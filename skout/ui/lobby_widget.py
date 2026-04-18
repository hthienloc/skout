# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from skout.ui.config import Theme
from skout.ui.card_widget import PillButton
from skout.engine.bot_logic import BotDifficulty

class LobbyWidget(QWidget):
    """
    KDE-style Lobby interface for Skout.
    Handles match configuration, player counts, and bot difficulty selection.
    """
    start_match = Signal(dict)  # Emits config dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bot_selectors = []
        self._setup_ui()

    def _setup_ui(self):
        """Initializes the lobby layout and widgets."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # 1. Title Section
        title = QLabel("SKOUT")
        title.setStyleSheet(f"font-size: {Theme.FONT_SIZE_TITLE}px; font-weight: bold; color: palette(highlight);")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        tagline = QLabel("Fast-paced strategy card game")
        tagline.setStyleSheet(f"font-size: 16px; color: {Theme.TEXT_SECONDARY};")
        tagline.setAlignment(Qt.AlignCenter)
        layout.addWidget(tagline)

        # 2. Configuration Section
        config_box = QWidget()
        config_box.setMinimumWidth(400)
        self.config_layout = QVBoxLayout(config_box)
        self.config_layout.setSpacing(15)
        
        # Player Count
        player_count_layout = QHBoxLayout()
        label_player_count = QLabel("Number of players:")
        label_player_count.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        
        self.spin_player_count = QSpinBox()
        self.spin_player_count.setRange(2, 5)
        self.spin_player_count.setValue(5)
        self.spin_player_count.setMinimumHeight(35)
        self.spin_player_count.valueChanged.connect(self._rebuild_bot_configs)
        
        player_count_layout.addWidget(label_player_count)
        player_count_layout.addStretch()
        player_count_layout.addWidget(self.spin_player_count)
        self.config_layout.addLayout(player_count_layout)

        # Bots Container
        self.bot_container = QWidget()
        self.bot_vbox = QVBoxLayout(self.bot_container)
        self.bot_vbox.setContentsMargins(0, 0, 0, 0)
        self.config_layout.addWidget(self.bot_container)
        
        layout.addWidget(config_box, 0, Qt.AlignCenter)

        # 3. Action Section
        btns_row = QHBoxLayout()
        btns_row.setSpacing(20)
        
        self.spectate_mode = False
        self.btn_spectate = PillButton("SPECTATE MODE")
        self.btn_spectate.clicked.connect(self._on_toggle_spectate)
        btns_row.addWidget(self.btn_spectate)

        self.btn_start = PillButton("START MATCH", primary=True)
        self.btn_start.setMinimumWidth(200)
        self.btn_start.clicked.connect(self._on_start_clicked)
        btns_row.addWidget(self.btn_start)
        
        layout.addLayout(btns_row)
        
        self._rebuild_bot_configs()

    def _rebuild_bot_configs(self):
        """Standardizing dynamic bot allocation logic."""
        # Clear existing
        while self.bot_vbox.count():
            item = self.bot_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

        num_players = self.spin_player_count.value()
        self.bot_selectors = []

        for i in range(2, num_players + 1):
            row = QHBoxLayout()
            lbl = QLabel(f"Bot {i-1} grade:")
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
            
            combo = QComboBox()
            combo.setMinimumHeight(35)
            combo.setMinimumWidth(150)
            for diff in BotDifficulty:
                combo.addItem(diff.value, diff)
            
            # Default logic
            if i >= 4: combo.setCurrentIndex(2)
            elif i >= 3: combo.setCurrentIndex(1)
            else: combo.setCurrentIndex(0)
            
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(combo)
            self.bot_vbox.addLayout(row)
            self.bot_selectors.append(combo)

    def _clear_sub_layout(self, layout):
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
                if item.layout(): self._clear_sub_layout(item.layout())

    def _on_toggle_spectate(self):
        self.spectate_mode = not self.spectate_mode
        self.btn_spectate.setText("VIEWER" if self.spectate_mode else "SPECTATE MODE")

    def _on_start_clicked(self):
        config = {
            "player_count": self.spin_player_count.value(),
            "spectate": self.spectate_mode,
            "bot_difficulties": [c.currentData() for c in self.bot_selectors]
        }
        self.start_match.emit(config)

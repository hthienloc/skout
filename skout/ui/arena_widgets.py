# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QGridLayout, QPushButton, QApplication
)
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath, QPalette, QIcon
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from skout.ui.config import Theme, Assets

class CircularAvatar(QLabel):
    def __init__(self, difficulty_name: str, size: int = 80):
        super().__init__()
        self.setFixedSize(size, size)
        
        # Determine content
        self.content = Assets.AVATARS.get(difficulty_name, "user-identity")
        self.pixmap = None
        
        icon = QIcon.fromTheme(self.content)
        if not icon.isNull():
            self.pixmap = icon.pixmap(size, size)
        else:
            # Local fallback or standard player path
            self.pixmap = QPixmap(self.content).scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Consistent frameless icon rendering
        if self.pixmap:
            # Clip to circle for a polished look if needed
            path = QPainterPath()
            path.addEllipse(self.rect())
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, self.pixmap)

class PlayerSeat(QFrame):
    def __init__(self, player_id: str, difficulty_name: str):
        super().__init__()
        self.player_id = player_id
        self.difficulty = difficulty_name
        self.setFixedWidth(Theme.SEAT_MAX_WIDTH)
        
        self.init_ui()
        
    @property
    def is_human(self) -> bool:
        return self.difficulty == "Human"
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(5)
        
        # Avatar & Token Container
        self.avatar_container = QWidget()
        self.avatar_layout = QGridLayout(self.avatar_container)
        self.avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Avatar
        self.avatar = CircularAvatar(self.difficulty, Theme.SEAT_AVATAR_SIZE)
        self.avatar_layout.addWidget(self.avatar, 0, 0, Qt.AlignCenter)
        
        # S&S Chip (Floating Badge)
        self.ss_chip = QLabel("⚡")
        self.ss_chip.setFixedSize(28, 28)
        self.ss_chip.setAlignment(Qt.AlignCenter)
        self.ss_chip.setStyleSheet(f"""
            QLabel {{
                background: {Theme.COLOR_COMBO};
                color: white;
                border: 2px solid white;
                border-radius: 14px;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        # Position badge at bottom right of avatar
        self.avatar_layout.addWidget(self.ss_chip, 0, 0, Qt.AlignBottom | Qt.AlignRight)
        
        self.main_layout.addWidget(self.avatar_container, 0, Qt.AlignCenter)
        
        # Info Box (Themed)
        self.info_box = QFrame()
        self.info_box.setObjectName("info-box")
        self.info_box.setStyleSheet(f"""
            QFrame#info-box {{
                background: {Theme.BG_GLASS};
                border-radius: 8px;
                border: 1px solid {Theme.CARD_BORDER};
            }}
        """)
        
        self.info_layout = QVBoxLayout(self.info_box)
        self.info_layout.setContentsMargins(10, 5, 10, 5)
        self.info_layout.setSpacing(2)
        
        self.lbl_name = QLabel(self.player_id)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 13px;")
        self.info_layout.addWidget(self.lbl_name)
        
        self.stats_row = QHBoxLayout()
        
        self.lbl_score = QLabel("0 VP")
        self.lbl_score.setStyleSheet(f"color: {Theme.TEXT_GOLD}; font-weight: bold;")
        
        self.lbl_hand = QLabel(" 0")
        self.lbl_hand.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        
        self.stats_row.addWidget(self.lbl_score)
        self.stats_row.addStretch()
        self.stats_row.addWidget(self.lbl_hand)
        
        self.info_layout.addLayout(self.stats_row)
        self.main_layout.addWidget(self.info_box)
        
        # Turn Indicator (Spotlight)
        self.setStyleSheet("border: 2px solid transparent;")

    def update_stats(self, score: int, hand_count: int, is_current: bool, ss_available: bool):
        self.lbl_score.setText(f"{score} VP")
        self.lbl_hand.setText(f" {hand_count}")
        self.ss_chip.setVisible(ss_available)
        
        # Turn Indicator (System Highlight)
        if is_current:
            self.info_box.setStyleSheet(f"""
                QFrame#info-box {{
                    background: palette(highlight);
                    border-radius: 8px;
                    border: 1px solid palette(highlight);
                }}
            """)
            self.lbl_name.setStyleSheet("color: palette(highlighted-text); font-weight: bold;")
            self.lbl_score.setStyleSheet("color: palette(highlighted-text);")
            self.lbl_hand.setStyleSheet("color: palette(highlighted-text);")
        else:
             self.info_box.setStyleSheet(f"""
                QFrame#info-box {{
                    background: {Theme.BG_GLASS};
                    border-radius: 8px;
                    border: 1px solid {Theme.CARD_BORDER};
                }}
            """)
             self.lbl_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold;")
             self.lbl_score.setStyleSheet(f"color: {Theme.TEXT_GOLD};")
             self.lbl_hand.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")

class ArenaLog(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 200)
        self.setObjectName("arena-log")
        self.setStyleSheet(f"""
            QFrame#arena-log {{
                background: palette(base);
                border-radius: 12px;
                border: 1px solid {Theme.CARD_BORDER};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Header Row: Title + Copy Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        lbl_title = QLabel("PERFORMANCE LOG")
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_GOLD}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()
        
        self.btn_copy = QPushButton("COPY")
        self.btn_copy.setFixedSize(45, 18)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background: palette(alternate-base);
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.CARD_BORDER};
                border-radius: 4px;
                font-size: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: palette(highlight);
                color: palette(highlighted-text);
            }}
        """)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        header_layout.addWidget(self.btn_copy)
        
        self.layout.addLayout(header_layout)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Minimalist
        
        self.log_widget = QWidget()
        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(4)
        self.log_layout.addStretch()
        
        self.scroll.setWidget(self.log_widget)
        self.layout.addWidget(self.scroll)
        
        self.entries = []

    def copy_to_clipboard(self):
        """Copies all log entries to the system clipboard."""
        text = "\n".join([lbl.text() for lbl in self.entries])
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            
            # Feedback
            self.btn_copy.setText("DONE")
            self.btn_copy.setStyleSheet(self.btn_copy.styleSheet().replace(Theme.TEXT_SECONDARY, "#2ecc71"))
            QTimer.singleShot(1500, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.btn_copy.setText("COPY")
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background: palette(alternate-base);
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.CARD_BORDER};
                border-radius: 4px;
                font-size: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: palette(highlight);
                color: palette(highlighted-text);
            }}
        """)

    def add_entry(self, text: str, color: str = None):
        # Use explicit window-text palette for maximum contrast
        style = "font-size: 11px; font-weight: 500;"
        if color:
            style += f" color: {color};"
        else:
            style += " color: palette(window-text);"
            
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(style)
        
        # Insert before the stretch
        self.log_layout.insertWidget(self.log_layout.count() - 1, lbl)
        self.entries.append(lbl)
        
        # Scroll to bottom
        QTimer.singleShot(10, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
        
        # Limit entries
        if len(self.entries) > 50:
            old = self.entries.pop(0)
            old.deleteLater()

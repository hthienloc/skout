# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

import os

class Assets:
    _UI_DIR = os.path.dirname(__file__)
    _ROOT = os.path.dirname(os.path.dirname(_UI_DIR))
    _BASE = os.path.join(_ROOT, "assets", "avatars")
    
    AVATARS = {
        "Easy": "face-smile",
        "Middle": "face-glasses",
        "Hard": "face-ninja",
        "Human": "user-identity"
    }

    ICONS = {
        "New": "document-new",
        "Pause": "media-playback-pause",
        "Resume": "media-playback-start",
        "Rules": "help-contents",
        "Quit": "application-exit",
        "Lobby": "go-home"
    }

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

class Theme:
    @staticmethod
    def get_color(role: QPalette.ColorRole) -> str:
        try:
            return QApplication.palette().color(role).name()
        except:
            return "#ffffff"

    # --- COLORS (Dynamic) ---
    @property
    def BG_MAIN(self): return self.get_color(QPalette.Window)
    @property
    def BG_TABLE(self): 
        # Deep red/table green or system shadow
        return self.get_color(QPalette.Base)
    @property
    def BG_GLASS(self): return "rgba(255, 255, 255, 0.1)"
    @property
    def BG_GLASS_HOVER(self): return "rgba(255, 255, 255, 0.2)"
    @property
    def BG_HIGHLIGHT(self): return self.get_color(QPalette.Highlight)
    
    # Text
    @property
    def TEXT_PRIMARY(self): return self.get_color(QPalette.WindowText)
    @property
    def TEXT_SECONDARY(self): 
        col = QApplication.palette().color(QPalette.WindowText)
        col.setAlpha(180)
        return f"rgba({col.red()}, {col.green()}, {col.blue()}, 180)"
    @property
    def TEXT_GOLD(self): return "#f1c40f" # Characteristic gold for Skout
    @property
    def TEXT_DISABLED(self): 
        col = QApplication.palette().color(QPalette.WindowText)
        col.setAlpha(80)
        return f"rgba({col.red()}, {col.green()}, {col.blue()}, 80)"
    
    # Action Colors
    @property
    def COLOR_SHOW(self): return "#e74c3c"
    @property
    def COLOR_SKOUT(self): return "#f39c12"
    @property
    def COLOR_COMBO(self): return self.get_color(QPalette.Highlight)
    @property
    def COLOR_CANCEL(self): return "#95a5a6"
    @property
    def COLOR_FLIP(self): return "#e67e22"
    @property
    def COLOR_CONFIRM(self): return "#2ecc71"
    @property
    def COLOR_DISABLED(self): return "rgba(0,0,0,0.1)"
    
    # Card Aesthetics
    @property
    def CARD_BG(self): return self.get_color(QPalette.Base)
    @property
    def CARD_HOVER(self): return self.get_color(QPalette.AlternateBase)
    @property
    def CARD_TEXT(self): return self.get_color(QPalette.Text)
    @property
    def CARD_BORDER(self): 
        col = QApplication.palette().color(QPalette.Mid)
        return col.name()
    @property
    def CARD_HIGHLIGHT(self): return self.get_color(QPalette.Highlight)
    @property
    def CARD_STAGED(self): return self.get_color(QPalette.Highlight)
    
    @property
    def COLOR_DROP_ZONE(self): 
        col = QApplication.palette().color(QPalette.Highlight)
        return f"rgba({col.red()}, {col.green()}, {col.blue()}, 0.2)"
    @property
    def COLOR_DROP_ZONE_HOVER(self):
        col = QApplication.palette().color(QPalette.Highlight)
        return f"rgba({col.red()}, {col.green()}, {col.blue()}, 0.5)"
    
    # Static values can stay as class attributes
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 850
    CARD_WIDTH = 75
    CARD_HEIGHT = 115
    CARD_RADIUS = 8
    TABLE_HEIGHT = 360
    RING_BORDER = 4
    RING_RADIUS = 30
    PANEL_PADDING = 15
    PANEL_SPACING = 15
    SCOREBOARD_MAX_HEIGHT = 140
    HAND_PANEL_MIN_HEIGHT = 240
    DROP_ZONE_WIDTH = 18
    SEAT_MAX_WIDTH = 170
    SEAT_AVATAR_SIZE = 70
    ARENA_POSITIONS = {0:(2,1), 1:(1,2), 2:(0,2), 3:(0,1), 4:(0,0), 5:(1,0)}
    FONT_FAMILY = "Inter" if "linux" in __import__('sys').platform else "Segoe UI"
    FONT_SIZE_TITLE = 42
    FONT_SIZE_LABEL = 13
    FONT_SIZE_CARD_TOP = 20
    FONT_SIZE_CARD_BOT = 14
    FONT_SIZE_BUTTON = 11
    BOT_DELAY_MS = 1500
    ANIMATION_SPEED = 250

    def get_font_family(self):
        return self.FONT_FAMILY

# Global Theme Instance
Theme = Theme()

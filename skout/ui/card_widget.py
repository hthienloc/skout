# SPDX-FileCopyrightText: 2026 Loc Huynh <huynhloc.contact@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QPoint
from PySide6.QtGui import QColor, QFont
from skout.ui.config import Theme
from skout.core.card import Card

class PremiumCard(QFrame):
    clicked = Signal(int)

    def __init__(self, card: Card, index: int, parent=None):
        super().__init__(parent)
        self.card = card
        self.index = index
        self.skoutable = False
        self.setFixedSize(Theme.CARD_WIDTH, Theme.CARD_HEIGHT)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        self.lbl_top = QLabel(str(card.top_value))
        self.lbl_top.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_top.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_CARD_TOP, QFont.Bold))
        
        self.lbl_bot = QLabel(str(card.bottom_value))
        self.lbl_bot.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.lbl_bot.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_CARD_BOT, QFont.Bold))
        
        self.layout.addWidget(self.lbl_top)
        self.layout.addWidget(self.lbl_bot)
        
        self._apply_base_style()
        
    def _apply_base_style(self):
        """Resets style and graphics effects to default."""
        self.setGraphicsEffect(None)
        self.setCursor(Qt.ArrowCursor)
        self.lbl_top.setStyleSheet(f"color: {Theme.CARD_TEXT}; border: none; background: transparent;")
        self.lbl_bot.setStyleSheet(f"color: {Theme.CARD_TEXT}; opacity: 0.6; border: none; background: transparent;")
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.CARD_BG};
                border: 1px solid {Theme.CARD_BORDER};
                border-radius: {Theme.CARD_RADIUS}px;
            }}
            QFrame[selected="true"] {{
                background-color: {Theme.CARD_HOVER};
                border: 2px solid {Theme.CARD_HIGHLIGHT};
            }}
        """)
        
        # Standard Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(2)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)

    def update_card(self, card_obj: Card, index: int):
        self.card = card_obj
        self.index = index
        self.skoutable = False
        self.lbl_top.setText(str(card_obj.top_value))
        self.lbl_bot.setText(str(card_obj.bottom_value))
        self._apply_base_style()
        self.set_selected(False)
        self.update()

    def set_selected(self, selected: bool):
        """Efficiently toggles selection via dynamic property."""
        val = "true" if selected else "false"
        if self.property("selected") == val: return
        self.setProperty("selected", val)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_staged(self, is_staged: bool):
        """Visual feedback for cards chosen during a combo."""
        if not is_staged:
            self._apply_base_style()
            return

        self.lbl_top.setStyleSheet(f"color: {Theme.CARD_TEXT}; opacity: 0.8; border: none; background: transparent;")
        self.lbl_bot.setStyleSheet(f"color: {Theme.CARD_TEXT}; opacity: 0.4; border: none; background: transparent;")
        
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(15)
        effect.setColor(QColor(Theme.CARD_STAGED))
        effect.setOffset(0, 0)
        self.setGraphicsEffect(effect)
        self.setStyleSheet(f"QFrame {{ background-color: {Theme.CARD_BG}; border: 3px dashed {Theme.CARD_STAGED}; border-radius: {Theme.CARD_RADIUS}px; }}")

    def enterEvent(self, event):
        try:
            if not self.skoutable and hasattr(self, 'shadow') and self.shadow:
                self.shadow.setBlurRadius(30)
            # Only change BG if not in a special state
            if not self.skoutable:
                self.setStyleSheet(self.styleSheet().replace(Theme.CARD_BG, Theme.CARD_HOVER))
        except (RuntimeError, AttributeError): pass

    def leaveEvent(self, event):
        try:
            if not self.skoutable and hasattr(self, 'shadow') and self.shadow:
                self.shadow.setYOffset(4)
                self.shadow.setBlurRadius(15)
            if not self.skoutable:
                self.setStyleSheet(self.styleSheet().replace(Theme.CARD_HOVER, Theme.CARD_BG))
        except (RuntimeError, AttributeError): pass

    def set_skoutable(self, skoutable: bool):
        if self.skoutable == skoutable: return
        self.skoutable = skoutable
        
        if skoutable:
            self.setCursor(Qt.PointingHandCursor)
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(15)
            effect.setColor(QColor(Theme.CARD_STAGED))
            effect.setOffset(0, 0)
            self.setGraphicsEffect(effect)
            self.setStyleSheet(f"QFrame {{ background-color: {Theme.CARD_BG}; border: 3px dashed {Theme.CARD_STAGED}; border-radius: {Theme.CARD_RADIUS}px; }}")
        else:
            self._apply_base_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)

    def shake(self):
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(200)
        curr = self.pos()
        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.2, curr + QPoint(-5, 0))
        anim.setKeyValueAt(0.4, curr + QPoint(5, 0))
        anim.setKeyValueAt(0.6, curr + QPoint(-5, 0))
        anim.setKeyValueAt(0.8, curr + QPoint(5, 0))
        anim.setKeyValueAt(1.0, curr)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

class GlassPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_GLASS};
                border: 1px solid {Theme.BG_GLASS_HOVER};
                border-radius: {Theme.CARD_RADIUS}px;
            }}
        """)

class DropZone(QPushButton):
    dropped = Signal(int)
    def __init__(self, index: int, parent=None):
        super().__init__("", parent)
        self.target_index = index
        self.setFixedWidth(Theme.DROP_ZONE_WIDTH)
        self.setFixedHeight(Theme.CARD_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px dashed {Theme.COLOR_DROP_ZONE};
                border-radius: {Theme.CARD_RADIUS // 2}px;
            }}
            QPushButton:hover {{
                background: {Theme.COLOR_DROP_ZONE_HOVER};
                border: 2px solid {Theme.COLOR_SKOUT};
            }}
        """)
        self.clicked.connect(lambda: self.dropped.emit(self.target_index))

class PillButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.setFixedHeight(36)
        self.setMinimumWidth(120)
        self.setFont(QFont(Theme.get_font_family(), Theme.FONT_SIZE_BUTTON))
        self.setCursor(Qt.PointingHandCursor)
        
        # Standardized KDE-aligned button style using System Palette
        if primary:
            # High-visibility primary action
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: palette(highlight);
                    color: palette(highlighted-text);
                    border: none;
                    border-radius: 6px;
                    padding: 0px 16px;
                }}
                QPushButton:hover {{
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 palette(highlight), stop:1 palette(link));
                }}
            """)
        else:
            # Standard secondary action
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: palette(button);
                    color: palette(button-text);
                    border: 1px solid {Theme.CARD_BORDER};
                    border-radius: 6px;
                    padding: 0px 16px;
                }}
                QPushButton:hover {{
                    background-color: palette(highlight);
                    color: palette(highlighted-text);
                    border: 1px solid palette(highlight);
                }}
            """)
            
        self.setStyleSheet(self.styleSheet() + """
            QPushButton:disabled {
                background-color: palette(light);
                color: palette(disabled-text);
                opacity: 0.5;
            }
        """)

# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
    QToolBar, QMessageBox, QSizePolicy, QDialog, QTextBrowser, QPushButton
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QTimer, Qt, QSize

from skout.ui.config import Theme, Assets
from skout.ui.lobby_widget import LobbyWidget
from skout.ui.arena_manager import ArenaWidget
from skout.engine.engine import GameEngine
from skout.engine.bot_logic import SkoutBot

class RulesDialog(QDialog):
    """A custom dialog to display game rules with proper Markdown rendering."""
    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SKOUT Rules")
        self.resize(850, 700)
        
        layout = QVBoxLayout(self)
        
        self.browser = QTextBrowser()
        self.browser.setMarkdown(content)
        self.browser.setOpenExternalLinks(True)
        # Ensure smooth scrolling and readable text
        self.browser.setStyleSheet(f"background-color: transparent; color: {Theme.TEXT_PRIMARY}; font-size: 14px; padding: 10px;")
        
        layout.addWidget(self.browser)
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setFixedWidth(120)
        layout.addWidget(self.btn_close, alignment=Qt.AlignCenter)

class SkoutMainWindow(QMainWindow):
    """
    Main Application Window for SKOUT.
    Orchestrates transitions between the Lobby and the Game Arena.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SKOUT")
        self.setWindowIcon(QIcon.fromTheme("org.kde.skout"))
        self.resize(Theme.WINDOW_WIDTH, Theme.WINDOW_HEIGHT)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Initialize Modular Widgets
        self.lobby = LobbyWidget()
        self.arena = ArenaWidget()
        
        self.stack.addWidget(self.lobby)
        self.stack.addWidget(self.arena)
        
        # Connections
        self.lobby.start_match.connect(self.on_start_match)
        self.arena.back_to_lobby.connect(self.on_back_to_lobby)
        self.arena.status_message.connect(self.statusBar().showMessage)
        
        self.stack.setCurrentIndex(0)
        
        # 3. UI Components (Standard KDE layout)
        self._init_actions()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Game Tick Timer (Coordinates bot actions)
        self.timer = QTimer()
        self.timer.timeout.connect(self.arena.on_tick)
        self.timer.start(Theme.BOT_DELAY_MS)

    def _init_actions(self):
        """Initializes all shared actions for menus and toolbars."""
        # New Match
        self.act_new = QAction(QIcon.fromTheme(Assets.ICONS["New"]), "&New Match", self)
        self.act_new.setShortcut("Ctrl+N")
        self.act_new.triggered.connect(self.on_back_to_lobby)

        # High Scores
        self.act_high_scores = QAction(QIcon.fromTheme("games-highscores"), "&High Scores", self)
        self.act_high_scores.setShortcut("Ctrl+H")
        self.act_high_scores.triggered.connect(self._on_high_scores_clicked)

        # Quit
        self.act_quit = QAction(QIcon.fromTheme(Assets.ICONS["Quit"]), "&Quit", self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.close)

        # Pause/Resume
        self.act_pause = QAction(QIcon.fromTheme(Assets.ICONS["Pause"]), "&Pause", self)
        self.act_pause.setShortcut("P")
        self.act_pause.setCheckable(True)
        self.act_pause.triggered.connect(self._on_pause_toggled)

        # Rules
        self.act_rules = QAction(QIcon.fromTheme(Assets.ICONS["Rules"]), "Skout &Handbook", self)
        self.act_rules.setShortcut("F1")
        self.act_rules.triggered.connect(self._on_rules_clicked)

        # About Qt
        self.act_about_qt = QAction("About &Qt", self)
        self.act_about_qt.triggered.connect(lambda: QMessageBox.aboutQt(self))

    def _setup_menubar(self):
        """Initializes the standard Menu Bar."""
        menubar = self.menuBar()
        
        # Game Menu
        game_menu = menubar.addMenu("&Game")
        game_menu.addAction(self.act_new)
        game_menu.addAction(self.act_high_scores)
        game_menu.addSeparator()
        game_menu.addAction(self.act_quit)

        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        self.act_show_toolbar = settings_menu.addAction("Show &Toolbar")
        self.act_show_toolbar.setCheckable(True)
        self.act_show_toolbar.setChecked(True)
        self.act_show_toolbar.triggered.connect(lambda checked: self.toolbar.setVisible(checked))

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.act_rules)
        help_menu.addSeparator()
        help_menu.addAction(self.act_about_qt)

    def _setup_toolbar(self):
        """Initializes the top toolbar with standard actions."""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.toolbar.addAction(self.act_new)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_pause)
        self.toolbar.addAction(self.act_rules)

    def _setup_statusbar(self):
        """Initializes the status bar."""
        self.statusBar().showMessage("Ready")

    def _on_pause_toggled(self, paused: bool):
        """Toggles the bot execution timer."""
        if paused:
            self.timer.stop()
            self.act_pause.setIcon(QIcon.fromTheme(Assets.ICONS["Resume"]))
            self.act_pause.setText("Resume Bots")
            self.statusBar().showMessage("Game Paused")
        else:
            self.timer.start(Theme.BOT_DELAY_MS)
            self.act_pause.setIcon(QIcon.fromTheme(Assets.ICONS["Pause"]))
            self.act_pause.setText("Pause")
            self.statusBar().showMessage("Resumed")

    def _on_rules_clicked(self):
        """Displays game rules in a custom dialog."""
        import os
        rules_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "rules.md")
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            dialog = RulesDialog(content, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load rules: {e}")

    def _on_high_scores_clicked(self):
        """Displays the High Scores dialog (Standard KDE feature)."""
        QMessageBox.information(self, "High Scores", "High Scores feature coming soon!\nStandardize your gameplay to reach the top.")

    def on_start_match(self, config: dict):
        """Initializes game engine and transitions to Arena."""
        engine = GameEngine()
        
        # 1. Add Players
        engine.add_player("You")
        for i in range(1, config["player_count"]):
            engine.add_player(f"Bot {i}")

        # 2. Build Bot Logic Map
        bots = {}
        # Human ID is "You"
        for i in range(1, config["player_count"]):
            bot_id = engine.players[i].id
            diff = config["bot_difficulties"][i-1]
            bots[bot_id] = SkoutBot(bot_id, difficulty=diff, player_count=config["player_count"])
            
        engine.start_round() # Setup deck and deals cards
        
        self.arena.start_game(engine, bots)
        self.stack.setCurrentIndex(1)
        self.statusBar().showMessage("Round Started")
        self.resize(Theme.WINDOW_WIDTH, Theme.WINDOW_HEIGHT)

    def on_back_to_lobby(self):
        """Returns to the setup screen."""
        self.stack.setCurrentIndex(0)
        self.statusBar().showMessage("Ready")
        self.resize(Theme.WINDOW_WIDTH, Theme.WINDOW_HEIGHT)

def main():
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    
    # Critical for Wayland: match the window to the .desktop file icon
    app.setDesktopFileName("org.kde.skout")
    
    window = SkoutMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

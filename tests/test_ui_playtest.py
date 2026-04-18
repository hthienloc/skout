# SPDX-FileCopyrightText: 2026 Loc Huynh <huynhloc.contact@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from skout.ui.main_window import SkoutMainWindow
from skout.engine.engine import GamePhase
from skout.engine.rules import SkoutRules
from skout.core.card import Card, CardValue

def test_full_game_playtest(qtbot):
    """
    Consolidated Playtest: Verifies UI responsiveness, engine rules, 
    and bot progression in a single integrated test.
    """
    window = SkoutMainWindow()
    qtbot.addWidget(window)
    window.show()

    # Access internal widgets
    lobby = window.lobby
    arena = window.arena

    # 1. LOBBY VERIFICATION
    assert window.stack.currentIndex() == 0
    # Search for TITLE label in lobby (it's internal now)
    
    # 2. START MATCH
    qtbot.mouseClick(lobby.btn_start, Qt.LeftButton)
    assert window.stack.currentIndex() == 1
    engine = arena.engine
    
    # 2.5 HANDLE ORIENTATION CHOICE
    if engine.phase == GamePhase.ORIENTATION_CHOICE:
        # Bots confirm in arena.on_tick
        arena.on_tick()
        # Human confirms manually
        qtbot.mouseClick(arena.btn_confirm, Qt.LeftButton)
    
    assert engine.phase == GamePhase.PLAYING

    # 2.6 FORCE HUMAN TURN
    engine.current_player_idx = 0
    arena.update_ui(force=True)
    assert engine.current_player.id == "You"

    # 3. ENGINE RULES VERIFICATION (Injected Play)
    p1 = engine.players[0]
    p1.hand.cards = [Card(1, CardValue(5, 5)), Card(2, CardValue(5, 5))]
    assert SkoutRules.is_valid_group(p1.hand.cards)
    
    # 4. UI INTERACTION: Select Cards
    arena.selected_indices = [0, 1]
    arena.update_ui(force=True)
    assert arena.btn_show.isEnabled()

    # 5. EXECUTE MOVE: Click SHOW
    qtbot.mouseClick(arena.btn_show, Qt.LeftButton)
    assert len(engine.current_trick.cards) == 2
    assert len(p1.hand) == 0
    assert arena.selected_indices == []

    # 6. BOT PROGRESSION VERIFICATION
    arena.on_tick() 
    assert engine.turn_count > 0

    # 7. CLEANUP LOGIC
    qtbot.mouseClick(arena.btn_confirm, Qt.LeftButton) # (Placeholder if game ends)
    window.on_back_to_lobby()
    assert window.stack.currentIndex() == 0
    # Seats are cleared in Arena.start_game or MainWindow logic? 
    # Current on_back_to_lobby just switches index.

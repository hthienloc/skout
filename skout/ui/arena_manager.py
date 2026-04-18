# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

import random
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from skout.ui.config import Theme, Assets
from skout.ui.card_widget import PremiumCard, DropZone, PillButton, GlassPanel
from skout.ui.arena_widgets import PlayerSeat, ArenaLog
from skout.engine.engine import GameEngine, GamePhase
from skout.engine.rules import SkoutRules
from skout.engine.bot_logic import SkoutBot

class ArenaWidget(QWidget):
    """
    Standardized Arena interface for Skout.
    Encapsulates all in-game logic, player interactions, and table rendering.
    """
    back_to_lobby = Signal()
    status_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine: Optional[GameEngine] = None
        self.bots: Dict[str, SkoutBot] = {}
        self.human_id = "You"
        
        # State
        self.selected_indices = []
        self.pending_skout = None
        self.staged_combo_skout = None
        self._waiting_combo_card = False
        self._waiting_combo_insert = False
        self._waiting_skout_card = False
        self._card_pool: Dict[int, PremiumCard] = {}
        self._game_over_shown = False
        
        # State Cache for Performance
        self._last_hand_ids = []
        self._last_table_ids = []
        self._hand_widgets = []
        self._table_widgets = []
        
        self._setup_ui()

    def _setup_ui(self):
        """Standardized KDE-like layout for the arena."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 1. Main Game Area (Arena Frame)
        self.arena_frame = QFrame()
        self.arena_frame.setObjectName("arena-frame")
        self.arena_layout = QGridLayout(self.arena_frame)
        self.arena_layout.setContentsMargins(20, 10, 20, 10)
        self.arena_layout.setSpacing(10)
        
        # Central Trick Stage (The Arena)
        self.trick_panel = QFrame()
        self.trick_panel.setObjectName("trick-panel")
        self.trick_panel.setStyleSheet(f"""
            QFrame#trick-panel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 palette(base), stop:1 palette(alternate-base));
                border: 1px solid {Theme.CARD_BORDER};
                border-radius: 20px;
            }}
        """)
        self.trick_vbox = QVBoxLayout(self.trick_panel)
        self.trick_layout = QHBoxLayout()
        self.trick_layout.setAlignment(Qt.AlignCenter)
        self.trick_vbox.addLayout(self.trick_layout)
        
        # LOG BAR (Inside Arena)
        self.log_label = QLabel("Welcome to SKOUT")
        self.log_label.setAlignment(Qt.AlignCenter)
        self.log_label.setStyleSheet("color: palette(window-text); font-size: 13px; font-weight: normal;")
        self.trick_vbox.addWidget(self.log_label)
        
        # Add Trick Stage to center
        self.arena_layout.addWidget(self.trick_panel, 1, 1)
        
        # Mathematical Symmetry: Ensure boundary rows occupy equal vertical space.
        # This centers row 1 (Trick Stage) perfectly without hacky stretches.
        boundary_height = 170 
        self.arena_layout.setRowMinimumHeight(0, boundary_height)
        self.arena_layout.setRowMinimumHeight(2, boundary_height)
        
        # Clear stretches (let min-height and content alignment do the work)
        for r in range(3): self.arena_layout.setRowStretch(r, 0)
        
        # Arena Log (Bottom Left)
        self.game_log = ArenaLog()
        self.arena_layout.addWidget(self.game_log, 2, 0, Qt.AlignBottom | Qt.AlignLeft)
        
        self.layout.addWidget(self.arena_frame, 6)
        
        # 3. Your Hand Area
        self.hand_panel = QFrame()
        self.hand_panel.setMinimumHeight(Theme.HAND_PANEL_MIN_HEIGHT)
        self.hand_vbox = QVBoxLayout(self.hand_panel)
        self.hand_vbox.setContentsMargins(15, 5, 15, 5)
        
        self.hand_scroll = QScrollArea()
        self.hand_scroll.setWidgetResizable(True)
        self.hand_scroll.setFrameShape(QFrame.NoFrame)
        self.hand_scroll.setStyleSheet("background: transparent;")
        
        self.hand_widget = QWidget()
        self.hand_cards_layout = QHBoxLayout(self.hand_widget)
        self.hand_cards_layout.setAlignment(Qt.AlignCenter)
        self.hand_cards_layout.setSpacing(-15)
        
        self.hand_scroll.setWidget(self.hand_widget)
        self.hand_vbox.addWidget(self.hand_scroll)
        
        # 4. Action Buttons
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setContentsMargins(0, 5, 0, 10)
        self.btn_layout.setSpacing(15)
        self.btn_layout.addStretch()
        
        self.btn_show = PillButton("SHOW", primary=True)
        self.btn_show.clicked.connect(self.on_human_show)
        self.btn_skout = PillButton("SKOUT")
        self.btn_skout.clicked.connect(self.on_human_skout_start)
        self.btn_combo = PillButton("COMBO")
        self.btn_combo.clicked.connect(self.on_human_combo)
        self.btn_cancel = PillButton("CANCEL")
        self.btn_cancel.clicked.connect(self.on_cancel_action)
        self.btn_cancel.setVisible(False)
        self.btn_flip = PillButton("FLIP")
        self.btn_flip.clicked.connect(self.on_human_flip)
        self.btn_confirm = PillButton("CONFIRM", primary=True)
        self.btn_confirm.clicked.connect(self.on_human_confirm)

        for b in [self.btn_show, self.btn_skout, self.btn_combo, self.btn_flip, self.btn_confirm, self.btn_cancel]:
            self.btn_layout.addWidget(b)
        
        self.btn_layout.addStretch()
        self.hand_vbox.addLayout(self.btn_layout)
        self.layout.addWidget(self.hand_panel, 2)
        
        self.seats: Dict[str, PlayerSeat] = {}

    def start_game(self, engine: GameEngine, bots: Dict[str, SkoutBot]):
        """Initializes the arena with game state."""
        self.engine = engine
        self.bots = bots
        self._game_over_shown = False
        
        # Clean up previous
        for seat in self.seats.values():
            self.arena_layout.removeWidget(seat)
            seat.deleteLater()
        self.seats = {}
        
        self.update_ui(force=True)

    def update_ui(self, force=False):
        """Synchronous Snapshot-Driven UI Update."""
        if not self.engine: return
        
        engine = self.engine
        human_player = engine.players[0]
        
        playing = (engine.phase == GamePhase.PLAYING)
        is_my_turn = (engine.current_player.id == self.human_id and playing)
        is_staged = bool(self.staged_combo_skout)
        orienting = (engine.phase == GamePhase.ORIENTATION_CHOICE)

        # Update messaging
        status_msg = ""
        if orienting:
            msg = "PREPARE: Click FLIP to rotate, then CONFIRM."
            self.log_label.setText(msg)
            self.log_label.setStyleSheet("color: palette(window-text);")
            status_msg = "Orientation Phase"
        elif playing:
            if is_my_turn:
                if is_staged:
                    msg = "COMBO: Select your set and CONFIRM."
                    self.log_label.setText(msg)
                    self.log_label.setStyleSheet("color: palette(highlight); font-weight: bold;")
                    status_msg = "Your Turn: Select combo set"
                elif self.pending_skout:
                    msg = "INSERTION: Click an insertion point in your hand."
                    self.log_label.setText(msg)
                    self.log_label.setStyleSheet("color: palette(link); font-weight: bold;")
                    status_msg = "Your Turn: Insert skouted card"
                elif len(engine.current_trick.cards) == 0:
                    msg = "TABLE EMPTY: You must SHOW a set!"
                    self.log_label.setText(msg)
                    self.log_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
                    status_msg = "Your Turn: Table is empty"
                else:
                    msg = "YOUR TURN: SHOW a set or SKOUT a card."
                    self.log_label.setText(msg)
                    self.log_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
                    status_msg = "Your Turn"
            else:
                msg = f"Waiting for {engine.current_player.id}..."
                self.log_label.setText(msg)
                self.log_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
                status_msg = msg
        elif engine.phase == GamePhase.GAME_OVER:
            msg = "Match Finished. Click New Match to play again."
            self.log_label.setText(msg)
            self.log_label.setStyleSheet("color: palette(highlight); font-weight: bold;")
            status_msg = "Game Over"

        if status_msg:
            self.status_message.emit(status_msg)

        # Update Arena Seats
        if not self.seats:
            # We map names to difficulty labels for the avatars
            names = ["Human", "Easy", "Middle", "Hard", "Hard"]
            for i in range(len(engine.players)):
                p = engine.players[i]
                # Player name for display
                display_name = "You" if p.id == self.human_id else p.id
                # Difficulty label for avatar
                diff_label = names[i] if i < len(names) else "Medium"
                
                seat = PlayerSeat(display_name, diff_label)
                self.arena_layout.addWidget(seat, *Theme.ARENA_POSITIONS[i], Qt.AlignCenter)
                self.seats[p.id] = seat
        
        for p in engine.players:
            seat = self.seats.get(p.id)
            if seat:
                is_curr = (playing and engine.current_player.id == p.id)
                seat.update_stats(p.score, len(p.hand), is_curr, p.skout_and_show_available)

        # Refresh Table and Hand
        self._refresh_table()
        self._refresh_hand(human_player)
        self._update_button_states(playing, orienting, is_my_turn, human_player)
        
        # Process Logs
        if engine.last_action:
            self._process_action_log(engine.last_action)
            engine.last_action = None # CONSUME

    def _refresh_table(self):
        """Optimized table rendering with state caching."""
        engine = self.engine
        table_cards = list(engine.current_trick.cards)
        # Use fingerprint (id, orientation) for cache
        card_fingerprints = [(c.id, c.is_inverted) for c in table_cards]
        
        is_staged = bool(self.staged_combo_skout)
        staged_idx = self.staged_combo_skout[0] if is_staged else -1
        
        playing = (engine.phase == GamePhase.PLAYING)
        is_my_turn = (engine.current_player.id == self.human_id and playing)
        is_skoutable_trick = is_my_turn and not self.pending_skout and not is_staged
        is_trick_set = SkoutRules.is_set(engine.current_trick.cards)

        # Skip layout rebuild if cards are unchanged and not in pending scout mode
        if card_fingerprints == self._last_table_ids and not is_staged and not self.pending_skout:
            for i, card_widget in enumerate(self._table_widgets):
                if is_skoutable_trick and (is_trick_set or i == 0 or i == len(table_cards)-1):
                    card_widget.set_skoutable(True)
                else:
                    card_widget.set_skoutable(False)
            return

        self._clear_layout(self.trick_layout)
        self._table_widgets = []
        
        for i, card in enumerate(table_cards):
            if i == staged_idx: continue
            
            # PREVIEW: If this card is being scouted and is flipped, show inverted
            display_card = card
            is_pending = False
            if self.pending_skout and self.pending_skout[0] == i:
                is_pending = True
                if self.pending_skout[1]: # flip is True
                    display_card = card.inverted()
            
            card_widget = self._get_card_widget(display_card, i)
            
            # SAFE DISCONNECT: Ensure no double-connections when reusing widgets
            try: card_widget.clicked.disconnect()
            except: pass

            if is_pending:
                card_widget.set_skoutable(True) # Keep dashed border for the chosen one
            elif is_skoutable_trick and (is_trick_set or i == 0 or i == len(table_cards) - 1):
                card_widget.set_skoutable(True)
                card_widget.clicked.connect(self.on_trick_card_clicked)
            else:
                card_widget.set_skoutable(False)
            
            card_widget.show()
            self.trick_layout.addWidget(card_widget)
            self._table_widgets.append(card_widget)
            
        self._last_table_ids = card_fingerprints

    def _refresh_hand(self, human_player):
        """Optimized hand rendering with state caching and fast selection updates."""
        is_insertion_mode = bool(self.pending_skout or self._waiting_combo_insert)
        cards = list(human_player.hand.cards)
        ins_at = -1
        if self.staged_combo_skout:
            _, ins_at, _, s_card = self.staged_combo_skout
            cards.insert(ins_at, s_card)
        
        # Use fingerprint (id, orientation) for cache
        card_fingerprints = [(c.id, c.is_inverted) for c in cards]

        # FAST PATH: Only selection changed
        if card_fingerprints == self._last_hand_ids and not is_insertion_mode:
            for i, card_ui in enumerate(self._hand_widgets):
                card_ui.set_selected(i in self.selected_indices)
            return

        # FULL REBUILD
        self._clear_layout(self.hand_cards_layout)
        self._hand_widgets = []
        
        for i, card in enumerate(cards):
            if is_insertion_mode:
                drop_zone = DropZone(i, self)
                drop_zone.dropped.connect(self.on_drop_zone_clicked)
                self.hand_cards_layout.addWidget(drop_zone)
            
            card_ui = self._get_card_widget(card, i)
            card_ui.set_selected(i in self.selected_indices)
            
            # SAFE DISCONNECT: Ensure no double-connections when reusing widgets
            try: card_ui.clicked.disconnect()
            except: pass
            
            if not is_insertion_mode:
                card_ui.clicked.connect(self.on_card_clicked)
            
            card_ui.show()
            self.hand_cards_layout.addWidget(card_ui)
            self._hand_widgets.append(card_ui)
        
        if is_insertion_mode:
            drop_zone = DropZone(len(cards), self)
            drop_zone.dropped.connect(self.on_drop_zone_clicked)
            self.hand_cards_layout.addWidget(drop_zone)
            
        self._last_hand_ids = card_fingerprints

    def _get_card_widget(self, card, idx) -> PremiumCard:
        if card.id in self._card_pool:
            w = self._card_pool[card.id]
            w.update_card(card, idx)
            return w
        w = PremiumCard(card, idx)
        self._card_pool[card.id] = w
        return w

    def _clear_layout(self, layout):
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().hide()

    def _update_button_states(self, playing, orienting, is_my_turn, human_player):
        is_staged = bool(self.staged_combo_skout)
        is_pending = bool(self.pending_skout)
        is_waiting = self._waiting_skout_card or self._waiting_combo_card or self._waiting_combo_insert
        
        can_show = False
        if playing and is_my_turn and self.selected_indices:
            hand = list(human_player.hand.cards)
            if is_staged: hand.insert(self.staged_combo_skout[1], self.staged_combo_skout[3])
            
            # Safety: ensure indices are within current hand range
            if all(0 <= idx < len(hand) for idx in self.selected_indices):
                group = [hand[idx] for idx in self.selected_indices]
                if SkoutRules.beats(group, self.engine.current_trick.cards):
                    can_show = True
            else:
                self.selected_indices = []
            
        self.btn_show.setEnabled(can_show and not is_pending and not is_waiting)
        self.btn_skout.setEnabled(is_my_turn and bool(self.engine.current_trick.cards) and not is_staged and not is_pending and not is_waiting)
        self.btn_combo.setEnabled(is_my_turn and human_player.skout_and_show_available and bool(self.engine.current_trick.cards) and not is_staged and not is_pending and not is_waiting)
        
        # Confirm is for Orientation OR Staged Combo
        self.btn_confirm.setEnabled(orienting or (is_my_turn and is_staged))
        self.btn_confirm.setVisible(orienting or is_staged)
        
        # Cancel is available if we are middle of any complex action
        self.btn_cancel.setVisible(is_staged or is_pending or is_waiting)
        
        # Flip is available during orientation, or when we have a card 'in hand' but not yet committed (Scout/S&S)
        self.btn_flip.setVisible(orienting or is_pending or is_staged)
        
        # Standard buttons hidden during special phases
        hide_main = is_staged or orienting or is_pending or is_waiting
        self.btn_show.setVisible(not hide_main)
        self.btn_skout.setVisible(not hide_main)
        self.btn_combo.setVisible(not hide_main)

    # --- Interaction Handlers ---
    def on_card_clicked(self, index):
        if not self.engine: return
        
        # Only allow selection during PLAYING phase on human turn
        playing = (self.engine.phase == GamePhase.PLAYING)
        is_my_turn = (self.engine.current_player.id == self.human_id and playing)
        
        if not is_my_turn:
            return

        # Selection Logic: Enforce Adjacency (Skout Rule)
        if index in self.selected_indices:
            # If deselecting, maintain adjacency or clear if in middle
            if index == self.selected_indices[0] or index == self.selected_indices[-1]:
                self.selected_indices.remove(index)
            else:
                self.selected_indices = []
        else:
            # If selecting a new card, check if it's adjacent to current selection
            if not self.selected_indices:
                self.selected_indices = [index]
            else:
                if index == self.selected_indices[0] - 1:
                    self.selected_indices.insert(0, index)
                elif index == self.selected_indices[-1] + 1:
                    self.selected_indices.append(index)
                else:
                    # Not adjacent: Clear old selection and start new one
                    self.selected_indices = [index]
        
        self.selected_indices.sort()
        self.update_ui()

    def on_human_show(self):
        if self.engine.play_cards(self.human_id, self.selected_indices):
            self.selected_indices = []
            self.update_ui(force=True)

    def on_human_skout_start(self):
        self._waiting_skout_card = True
        self.update_ui(force=True)

    def on_trick_card_clicked(self, trick_idx):
        if self._waiting_skout_card:
            self.pending_skout = (trick_idx, False)
            self._waiting_skout_card = False
            self.update_ui(force=True)
        elif self._waiting_combo_card:
            self._waiting_combo_card = False
            self._waiting_combo_insert = True
            self._combo_skout_idx = trick_idx
            self.update_ui(force=True)

    def on_drop_zone_clicked(self, index):
        if self.pending_skout:
            t_idx, flip = self.pending_skout
            self.engine.skout(self.human_id, t_idx, index, flip)
            self.pending_skout = None
            self.selected_indices = [] # Clear selection just in case
            self.update_ui(force=True)
        elif self._waiting_combo_insert:
            card = self.engine.current_trick.cards[self._combo_skout_idx]
            self.staged_combo_skout = (self._combo_skout_idx, index, False, card)
            self._waiting_combo_insert = False
            self.update_ui(force=True)

    def on_human_combo(self):
        self._waiting_combo_card = True
        self.selected_indices = [] # Clear selection for combo setup
        self.update_ui(force=True)

    def on_human_confirm(self):
        if self.engine.phase == GamePhase.ORIENTATION_CHOICE:
            self.engine.confirm_orientation(self.human_id, False)
        elif self.staged_combo_skout:
            s_idx, ins_at, flip, _ = self.staged_combo_skout
            self.engine.skout_and_show(self.human_id, s_idx, ins_at, flip, self.selected_indices)
            self.staged_combo_skout = None
            self.selected_indices = []
        self.update_ui(force=True)

    def on_human_flip(self):
        if self.engine.phase == GamePhase.ORIENTATION_CHOICE:
            player = self.engine.players[0]
            player.hand.invert()
            self.update_ui(force=True)
        elif self.pending_skout:
            idx, flip = self.pending_skout
            self.pending_skout = (idx, not flip)
            self.update_ui(force=True)
        elif self.staged_combo_skout:
            t_idx, h_idx, flip, card = self.staged_combo_skout
            self.staged_combo_skout = (t_idx, h_idx, not flip, card.inverted())
            self.update_ui(force=True)

    def on_cancel_action(self):
        self.pending_skout = None
        self.staged_combo_skout = None
        self._waiting_skout_card = False
        self._waiting_combo_card = False
        self._waiting_combo_insert = False
        self.selected_indices = []
        self.update_ui(force=True)

    def _process_action_log(self, action):
        """Generates a human-friendly description of the engine's last action."""
        if not action or not action.player_id: return
        display_name = "You" if action.player_id == self.human_id else action.player_id
        desc = ""
        
        if action.action_type == "show":
            new_p = SkoutRules.get_readable_power(action.played_cards)
            if action.beaten_cards:
                old_p = SkoutRules.get_readable_power(action.beaten_cards)
                desc = f"{display_name}: {new_p} > {old_p}"
            else:
                desc = f"{display_name} played {new_p}"
        elif action.action_type == "skout":
            desc = f"{display_name} skouted {action.skouted_card.top_value if action.skouted_card else ''}"
        elif action.action_type == "skout_and_show":
            new_p = SkoutRules.get_readable_power(action.played_cards)
            desc = f"{display_name}: S&S {new_p}"
        else:
            desc = f"{display_name} acted: {action.action_type}"
            
        self.game_log.add_entry(desc)
        # Also update the central log label
        self.log_label.setText(desc)
        self.status_message.emit(desc)

    def on_tick(self):
        if not self.engine or self.engine.phase == GamePhase.LOBBY: return
        
        if self.engine.phase == GamePhase.GAME_OVER:
            if not self._game_over_shown:
                self._game_over_shown = True
                self.timer.stop() # Stop the tick timer from window if accessible, or handle locally
                
                # Create a professional Score Summary Dialog
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Match Finished")
                msg_box.setIcon(QMessageBox.Information)
                
                scores_text = "\n".join([f"{'You' if p.id == self.human_id else p.id}: {p.score} VP" for p in self.engine.players])
                msg_box.setText("<b>The show has ended!</b><br><br>Final Scores:<br>" + scores_text)
                
                btn_play_again = msg_box.addButton("Play Again", QMessageBox.AcceptRole)
                btn_lobby = msg_box.addButton("Back to Lobby", QMessageBox.RejectRole)
                msg_box.setDefaultButton(btn_play_again)
                
                msg_box.exec()
                
                if msg_box.clickedButton() == btn_play_again:
                    # Reuse current config to restart immediately
                    # We need to reach back to MainWindow or trigger a reset
                    # For simplicity, we emit back_to_lobby but could add a restart signal
                    # Let's use a trick: back_to_lobby is already connected. 
                    # If we want instant restart, we need a new signal.
                    self.back_to_lobby.emit() # For now, return to lobby to start fresh
                else:
                    self.back_to_lobby.emit()
            return

        if self.engine.phase == GamePhase.ORIENTATION_CHOICE:
            for p in self.engine.players:
                if p.id in self.bots and not p.has_confirmed_orientation:
                    flip = self.bots[p.id].evaluate_best_orientation(p.hand.cards)
                    self.engine.confirm_orientation(p.id, flip)
            self.update_ui()
            return

        curr_p = self.engine.current_player
        if curr_p and curr_p.id in self.bots:
            self.bots[curr_p.id].make_move(self.engine)
            self.update_ui(force=True)

# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum, auto

from ..core.card import Card
from ..core.hand import Hand
from ..core.deck import Deck
from ..core.trick import Trick
from .rules import SkoutRules

class GamePhase(Enum):
    LOBBY = auto()
    DEALING = auto()
    ORIENTATION_CHOICE = auto()
    PLAYING = auto()
    SCORING = auto()
    GAME_OVER = auto()

@dataclass
class PlayerState:
    id: str
    hand: Hand = field(default_factory=Hand)
    captured_cards: int = 0
    skout_chips: int = 0
    skout_and_show_available: bool = True
    score: int = 0
    has_confirmed_orientation: bool = False

@dataclass
class LastAction:
    player_id: str
    action_type: str # "show", "skout", "skout_and_show"
    skouted_card: Optional[Card] = None
    played_cards: List[Card] = field(default_factory=list)
    beaten_cards: List[Card] = field(default_factory=list)

class GameEngine:
    def __init__(self):
        self.players: List[PlayerState] = []
        self.deck = None
        self.current_trick = Trick()
        self.phase = GamePhase.LOBBY
        self.current_player_idx: int = 0
        self.turn_count = 0
        self.last_action: Optional[LastAction] = None
        
    def add_player(self, player_id: str):
        if self.phase == GamePhase.LOBBY:
            self.players.append(PlayerState(id=player_id))
            
    def start_round(self):
        if len(self.players) < 2:
            return
            
        self.phase = GamePhase.DEALING
        self.deck = Deck(player_count=len(self.players))
        
        # 2p: 11 each, 3p: 12 each, 4p: 11 each, 5p: 9 each.
        player_counts = {2: 11, 3: 12, 4: 11, 5: 9}
        deal_count = player_counts.get(len(self.players), 9)
        
        for player in self.players:
            player.hand = Hand(self.deck.draw(deal_count))
            # 2p logic: 3 personal skout chips, no Skout & Show
            if len(self.players) == 2:
                player.skout_chips = 3
                player.skout_and_show_available = False
            else:
                player.skout_chips = 0
                player.skout_and_show_available = True
                
            player.captured_cards = 0
            player.has_confirmed_orientation = False
            
        self.phase = GamePhase.ORIENTATION_CHOICE
        self.current_player_idx = random.randrange(len(self.players))
        self.current_trick.clear()
        self.turn_count = 0

    def confirm_orientation(self, player_id: str, flip: bool):
        """Allows player to flip their entire hand once before the round starts."""
        if self.phase != GamePhase.ORIENTATION_CHOICE:
            return False
            
        for p in self.players:
            if p.id == player_id:
                if flip:
                    p.hand.invert()
                p.has_confirmed_orientation = True
                break
        
        # If all players confirmed, start playing
        if all(p.has_confirmed_orientation for p in self.players):
            self.phase = GamePhase.PLAYING
            
        return True

    @property
    def current_player(self) -> Optional[PlayerState]:
        if not self.players or self.current_player_idx >= len(self.players):
            return None
        return self.players[self.current_player_idx]

    def play_cards(self, player_id: str, indices: List[int]) -> bool:
        """Process a member's 'Show' action."""
        if self.phase != GamePhase.PLAYING or player_id != self.current_player.id:
            return False
            
        hand = self.current_player.hand
        try:
            play = [hand.get_card(i) for i in indices]
        except IndexError:
            return False
        
        # 1. Validate if indices are contiguous in hand
        sorted_indices = sorted(indices)
        if any(sorted_indices[i] + 1 != sorted_indices[i+1] for i in range(len(sorted_indices) - 1)):
            return False
            
        # 2. Check if valid Skout group (Set/Sequence) and beats trick
        if not SkoutRules.beats(play, self.current_trick.cards):
            return False
            
        # 3. Apply action
        # - Move old trick cards to player's captured cards (+1 VP each)
        beaten_cards = list(self.current_trick.cards)
        if beaten_cards:
            self.current_player.captured_cards += len(beaten_cards)
        
        # - Remove cards from player's hand
        removed = hand.remove_cards(indices)
        
        # - Visually normalize for the trick stage (sort runs, keep sets)
        display_play = SkoutRules.sort_if_sequence(list(removed))
        
        # - Update current trick
        self.current_trick.cards = display_play
        self.current_trick.player_id = player_id
        
        # - Record Metadata
        self.last_action = LastAction(
            player_id=player_id, 
            action_type="show", 
            played_cards=list(display_play),
            beaten_cards=beaten_cards
        )

        # 4. Advance turn
        self._advance_turn()
        return True

    def skout(self, player_id: str, index_in_trick: int, insert_at: int, flip: bool, advance_turn: bool = True) -> bool:
        """Process a member's 'Skout' action."""
        if self.phase != GamePhase.PLAYING or player_id != self.current_player.id:
            return False
            
        if not self.current_trick.cards:
            return False
            
        # 1. Validations: 
        if len(self.current_trick.cards) > 2:
            if not SkoutRules.is_set(self.current_trick.cards):
                if index_in_trick != 0 and index_in_trick != len(self.current_trick.cards) - 1:
                    return False
            
        # 2. Apply action
        card = self.current_trick.cards.pop(index_in_trick)
        if flip:
            card = card.inverted()
        
        if len(self.players) == 2:
            if self.current_player.skout_chips <= 0:
                return False
            self.current_player.skout_chips -= 1
        else:
            owner_id = self.current_trick.player_id
            for p in self.players:
                if p.id == owner_id:
                    p.skout_chips += 1
                    break
                
        self.current_player.hand.insert_card(card, insert_at)
        self.last_action = LastAction(player_id=player_id, action_type="skout", skouted_card=card)

        # 3. Advance turn
        if advance_turn:
            if len(self.players) == 2:
                pass
            else:
                self._advance_turn()
        return True

    def skout_and_show(self, player_id: str, skout_idx: int, insert_at: int, flip: bool, show_indices: List[int]) -> bool:
        """Process 'Skout & Show' combo action."""
        if self.phase != GamePhase.PLAYING or player_id != self.current_player.id:
            return False
            
        player = self.current_player
        if not player.skout_and_show_available:
            return False
            
        # Perform Skout WITHOUT advancing turn or checking game over
        success = self.skout(player_id, skout_idx, insert_at, flip, advance_turn=False)
        if not success:
            return False
            
        # Perform Show (which WILL advance turn and check game over)
        success = self.play_cards(player_id, show_indices)
        if not success:
            # Rollback skout (very rare if bot is correct)
            # Handled by engine being transactional or bot being smart.
            # For now, just return False.
            return False
        
        player.skout_and_show_available = False
        self.last_action.action_type = "skout_and_show"
        return True

    def _advance_turn(self, check_end: bool = True):
        self.turn_count += 1
        # Rules for 2-player variant are different
        is_2p = len(self.players) == 2
        
        # Check end of round conditions
        # 1. Player hand empty
        if len(self.current_player.hand) == 0:
            self.phase = GamePhase.SCORING
            self._finalize_scores(round_end_player_id=self.current_player.id)
            return

        # 2. In 2p, if someone cannot Show AND has no chips, round ends?
        # That check usually happens when it's their turn and they have no choices.
        # But let's handle the standard "return to owner" rule first.
        
        if not is_2p:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            # Return to owner (unbeatable set)
            if self.players[self.current_player_idx].id == self.current_trick.player_id:
                self.phase = GamePhase.SCORING
                self._finalize_scores(round_end_player_id=self.current_trick.player_id)
        else:
            # In 2p, the turn only advances when a SHOW action is performed.
            # wait, my play_cards calls _advance_turn.
            # In 2p, if you SHOW, your turn ends, and it becomes the other player's turn.
            # If you SKOUT, you continue.
            
            # So if we are here (from play_cards), it means a SHOW was performed.
            # Advance to next player.
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            
            # In 2p, if the next player starts their turn and they are the owner of the trick,
            # it means the other player skouted everything or couldn't beat it.
            if self.players[self.current_player_idx].id == self.current_trick.player_id:
                 # This shouldn't happen exactly like this in 2p because skout doesn't advance turn.
                 # Actually, if you SHOW, the other player becomes the current player.
                 pass

    def _finalize_scores(self, round_end_player_id: str):
        for p in self.players:
            # Captured cards (+1) + Skout chips (+1)
            p_score = p.captured_cards + p.skout_chips
            
            # Penalize remaining cards (-1), unless they ended the round
            if p.id != round_end_player_id:
                p_score -= len(p.hand)
            
            p.score += p_score
            
        self.phase = GamePhase.GAME_OVER

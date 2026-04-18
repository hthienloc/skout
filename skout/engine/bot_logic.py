# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from typing import List, Optional, Set
from enum import Enum
import random
from skout.engine.rules import SkoutRules
from skout.engine.engine import GameEngine, Trick
from skout.core.card import Card

class BotDifficulty(Enum):
    EASY = "Easy"
    MIDDLE = "Middle"
    HARD = "Hard"

class SkoutBot:
    def __init__(self, player_id: str, difficulty: BotDifficulty = BotDifficulty.MIDDLE, weights: dict = None, player_count: int = 5):
        self.player_id = player_id
        self.difficulty = difficulty
        self.player_count = player_count
        self.weights = weights or {
            "w_delta": 0.603, "w_capture": 1.769, "w_pressure": 1.660, 
            "w_potential": 2.745, "w_skout_cost": 5.006, "w_trash_bonus": 1.628,
            "w_rarity": 2.0
        }
        # Card tracking: counts of each value seen. 
        self.seen_counts: dict[int, int] = {i: 0 for i in range(1, 11)} 
        self.total_counts: dict[int, int] = self._calculate_total_counts(player_count)
        self.persistent_ids: set[int] = set() 
        # Deep Memory: Track exactly which cards players skouted
        self.observed_hands: dict[str, list[Card]] = {}
        # Superhuman Memory: How many turns has an opponent held a specific card ID?
        self.card_longevity: dict[int, int] = {} 
        self.last_processed_turn = -1

    def _calculate_total_counts(self, player_count: int) -> dict[int, int]:
        """Calculates exact deck composition based on game rules."""
        counts = {i: 9 for i in range(1, 11)}
        if player_count in [2, 4]:
            # Remove 9/10 card
            counts[9] = 8
            counts[10] = 8
        elif player_count == 3:
            # Remove all cards with a 10
            counts[10] = 0
            for i in range(1, 10):
                counts[i] = 8
        return counts

    def update_memory_visibility(self, engine: GameEngine):
        """Processes engine.last_action to update observed hands."""
        if engine.turn_count <= self.last_processed_turn:
            return
        
        # 1. Process standard visibility (hand + table)
        player = next((p for p in engine.players if p.id == self.player_id), None)
        hand_cards = player.hand.cards if player else []
        new_visible = list(hand_cards) + list(engine.current_trick.cards)
        for c in new_visible:
            if c.id not in self.persistent_ids:
                self.persistent_ids.add(c.id)
                self.seen_counts[c.values.top] += 1
                self.seen_counts[c.values.bottom] += 1

        # 2. Process Delta (last action)
        action = engine.last_action
        if action:
            # Increment longevity for all cards in all hands
            for card_list in self.observed_hands.values():
                for c in card_list:
                    self.card_longevity[c.id] = self.card_longevity.get(c.id, 0) + 1

            if action.player_id != self.player_id:
                if action.player_id not in self.observed_hands:
                    self.observed_hands[action.player_id] = []
                
                if action.action_type in ["skout", "skout_and_show"]:
                    if action.skouted_card:
                        self.observed_hands[action.player_id].append(action.skouted_card)
                        self.card_longevity[action.skouted_card.id] = 0 # New card
                
                if action.action_type in ["show", "skout_and_show"]:
                    # Remove played cards from our mental model of their hand
                    played_ids = {c.id for c in action.played_cards}
                    self.observed_hands[action.player_id] = [c for c in self.observed_hands[action.player_id] if c.id not in played_ids]
                    for pid in played_ids:
                        if pid in self.card_longevity: del self.card_longevity[pid]

        self.last_processed_turn = engine.turn_count

    def get_rarity_score(self, value: int) -> float:
        """Returns 0..1 score. 1.0 means it's the rarest (least of this value remains)."""
        remaining = self.total_counts[value] - self.seen_counts[value]
        if remaining <= 0: return 1.0
        return 1.0 - (remaining / 9.0)

    def evaluate_hand_strength(self, hand_cards: list[Card]) -> float:
        """
        Calculates hand strength using DP to find the best non-overlapping partition.
        This prevents double-counting and 'strength debt' for large sets.
        """
        if not hand_cards: return 0
        n = len(hand_cards)
        dp = [0.0] * (n + 1)
        w_rarity = self.weights.get("w_rarity", 2.0)

        for i in range(1, n + 1):
            # Option 1: Current card is trash/single (length 1 group)
            # Power of 1 card = 1.0
            dp[i] = dp[i-1] + 1.0 + self.get_rarity_score(hand_cards[i-1].top_value) * w_rarity
            
            # Option 2: Form a group ending at i
            # Limit length to 10 for performance (Skout hands are small anyway)
            for length in range(2, min(i, 10) + 1):
                group = hand_cards[i - length : i]
                if SkoutRules.is_valid_group(group):
                    # Power of length L group = L^2
                    # We use a slightly dampened multiplier for very long sets to avoid hoarding
                    power = (length ** 2.0)
                    if length >= 4: power *= 0.9 # Discourage infinite hoarding
                    
                    rarity_bonus = sum(self.get_rarity_score(c.top_value) for c in group) * w_rarity
                    current_strength = dp[i - length] + power + rarity_bonus
                    if current_strength > dp[i]:
                        dp[i] = current_strength
                        
        return dp[n]

    def evaluate_set_potential(self, cards: list[Card]) -> float:
        """Deep synergy analysis: detects bridges and seeds for massive sequences."""
        if not cards: return 0.0
        potential = 0.0
        values = [c.top_value for c in cards]
        
        # TIERED SYNERGY: Hard sees further
        lookahead_depth = 2 if self.difficulty == BotDifficulty.HARD else 1

        for i in range(len(values) - 1):
            v1, v2 = values[i], values[i+1]
            # Perfect Synergies
            if v1 == v2: potential += 1.0 # Immediate pair
            elif abs(v1 - v2) == 1: potential += 0.8 # Immediate sequence
            
            # Bridge Synergies (e.g., 5, [gap], 7)
            elif abs(v1 - v2) == 2: potential += 0.5 
            
            # Chain Momentum: 3+ cards already working together
            if i < len(values) - 2:
                v3 = values[i+2]
                if v1 == v2 == v3: potential += 2.0 # Triple seed
                elif (v1+1 == v2 and v2+1 == v3) or (v1-1 == v2 and v2-1 == v3):
                    potential += 1.5 # 3-Sequence seed

        # COMPRESSION BONUS: Is the hand getting 'Tighter'?
        # (Total range of values vs hand size)
        if len(values) > 1:
            hand_range = max(values) - min(values)
            density = len(values) / (hand_range + 1)
            potential += density * 5.0

        return potential

    def get_trash_indices(self, cards: List[Card]) -> List[int]:
        """Identifies indices of cards that don't belong to ANY valid group."""
        if not cards: return []
        if len(cards) == 1: return [0]
        trash = []
        for i in range(len(cards)):
            is_part_of_group = False
            if i > 0 and SkoutRules.is_valid_group([cards[i-1], cards[i]]): is_part_of_group = True
            if i < len(cards) - 1 and SkoutRules.is_valid_group([cards[i], cards[i+1]]): is_part_of_group = True
            if not is_part_of_group: trash.append(i)
        return trash

    def find_all_playable_groups(self, hand: list[Card], current_trick: Trick) -> list[dict]:
        plays = []
        for length in range(1, len(hand) + 1):
            for start in range(len(hand) - length + 1):
                indices = list(range(start, start + length))
                play = [hand[i] for i in indices]
                if SkoutRules.beats(play, current_trick.cards):
                    plays.append({
                        "indices": indices,
                        "play": play,
                        "power": SkoutRules.get_power_level(play),
                        "capture_count": len(current_trick.cards)
                    })
        return plays

    def predict_opponent_moves(self, engine: GameEngine, current_trick_cards: list[Card]) -> list[dict]:
        """Checks if ANY opponent can beat the current trick with known skouted cards."""
        all_plays = []
        for opponent in engine.players:
            if opponent.id == self.player_id: continue
            
            known_cards = self.observed_hands.get(opponent.id, [])
            if not known_cards: continue
            
            for length in range(1, len(known_cards) + 1):
                for start in range(len(known_cards) - length + 1):
                    play = known_cards[start : start + length]
                    if SkoutRules.beats(play, current_trick_cards):
                        all_plays.append({"player": opponent.id, "power": SkoutRules.get_power_level(play)})
        return all_plays

    def calculate_rarity_threats(self) -> dict[int, float]:
        """Returns a dict of value -> threat (0..1). Higher = more cards missing."""
        threats = {}
        for val in range(1, 11):
            missing = self.total_counts[val] - self.seen_counts[val]
            # If 3 or more of a value are missing, it's a major set threat
            threats[val] = min(1.0, missing / 4.0)
        return threats

    def table_survival_sim(self, engine: GameEngine, potential_play: list[Card], depth=0) -> float:
        """
        Hyper-intelligent lookahead using both known and inferred information.
        """
        if depth >= 3: return 1.0 
        
        # 1. KNOWN THREATS (Deterministic)
        opponents_who_can_beat = self.predict_opponent_moves(engine, potential_play)
        if opponents_who_can_beat:
            next_idx = (engine.current_player_idx + 1) % len(engine.players)
            next_player = engine.players[next_idx]
            if any(p["player"] == next_player.id for p in opponents_who_can_beat):
                return 0.05 # Fatal Trap
            return 0.3
            
        # 2. INFERRED THREATS (Probabilistic)
        threats = self.calculate_rarity_threats()
        play_power = SkoutRules.get_power_level(potential_play)
        
        # If we play a single card of value 5, and 4 cards of value 8 are missing...
        # and an opponent has a large hand, they MIGHT have that 8-set.
        for opponent in engine.players:
            if opponent.id == self.player_id: continue
            if len(opponent.hand) >= 5: # Large hands are dangerous
                # Find max rarity threat that could beat us
                for val, threat in threats.items():
                    # A set of missing cards beats our current play?
                    # (Simplified: if the value itself is higher and missing >= play length)
                    if val > potential_play[0].top_value and threat > 0.7:
                        # Statistical risk of being beaten by a hidden set
                        return 0.6 # Guarded Play
        
        return 1.0

    def choose_action(self, engine: GameEngine) -> dict:
        player = next((p for p in engine.players if p.id == self.player_id), None)
        if not player: return {}
        hand_cards = player.hand.cards
        opponents = [p for p in engine.players if p.id != self.player_id]
        current_strength = self.evaluate_hand_strength(hand_cards)
        
        # MEMORY REFRESH
        self.update_memory_visibility(engine)
        
        # AI TIERING
        w_delta, w_capture, w_pressure = self.weights["w_delta"], self.weights["w_capture"], self.weights["w_pressure"]
        w_skout_cost = self.weights["w_skout_cost"]
        w_trash_bonus = self.weights.get("w_trash_bonus", 2.0)
        w_potential = self.weights.get("w_potential", 3.0)
        
        adaptive_reason = "Standard Heuristics"
        hand_len = len(hand_cards)

        # ADAPTIVE PHASE DETECTION
        is_endgame = any(len(p.hand) <= 3 for p in engine.players)
        is_blitz = hand_len <= 4

        if self.difficulty == BotDifficulty.EASY:
            w_delta, w_capture, w_pressure = 1.5, 1.0, 0.5
            w_skout_cost = 2.0 
            adaptive_reason = "Passive Mode (EASY)"
        elif self.difficulty == BotDifficulty.MIDDLE:
            w_delta, w_capture, w_pressure = 0.8, 2.5, 0.8
            if is_endgame:
                w_capture += 2.0
                w_delta *= 1.2
            adaptive_reason = "Greedy Mode (MIDDLE)"
        elif self.difficulty == BotDifficulty.HARD:
            w_delta, w_capture, w_pressure = 0.4, 3.5, 2.0
            
            if is_blitz:
                w_delta *= 2.0 
                w_skout_cost *= 2.5 
                adaptive_reason = "ADAPT: Blitz Closer"
            elif is_endgame:
                w_capture += 4.0
                w_pressure *= 1.5
                adaptive_reason = "ADAPT: Endgame Pressure"
            else:
                adaptive_reason = "Champion Weights"
            
            # SABOTAGE: Block finish
            min_opp_hand = min([len(p.hand) for p in opponents]) if opponents else 10
            if min_opp_hand <= 2:
                w_capture += 8.0
                adaptive_reason += " + BLOCKING"

        # Pressure & Risk Calculation
        min_opp_hand = min([len(p.hand) for p in opponents]) if opponents else 10
        opp_ss_count = sum(1 for p in opponents if p.skout_and_show_available)
        
        panic_mult = 1.0
        if min_opp_hand <= 3: panic_mult = 2.5
        if min_opp_hand <= 2: panic_mult = 6.0
        if min_opp_hand <= 1: panic_mult = 15.0

        pressure = (10 - min_opp_hand) / 10.0
        pressure_bonus = pressure * w_pressure * panic_mult
        
        # ROUND END THREAT DETECTION
        is_round_end_threat = False
        if len(engine.players) > 2 and engine.current_trick.player_id:
            next_player_idx = (engine.current_player_idx + 1) % len(engine.players)
            if engine.players[next_player_idx].id == engine.current_trick.player_id:
                is_round_end_threat = True
                adaptive_reason = "ADAPT: Last Defense"

        choices = []
        trash_indices = self.get_trash_indices(hand_cards)

        # 1. EVALUATE SHOW
        possible_shows = self.find_all_playable_groups(hand_cards, engine.current_trick)
        for show in possible_shows:
            dummy_hand = [c for i, c in enumerate(hand_cards) if i not in show["indices"]]
            strength_loss = current_strength - self.evaluate_hand_strength(dummy_hand)
            trash_trimmed = len([idx for idx in show["indices"] if idx in trash_indices])
            
            # Base score: balance capture value vs strength loss
            score = (show["capture_count"] * w_capture * 5.0) - (strength_loss * w_delta)
            score += trash_trimmed * w_trash_bonus 
            
            # Hand reduction priority
            score += len(show["indices"]) * 12.0
            
            # Pressure scaling
            score += pressure_bonus * (show["power"] / 800.0)
            
            # Risk assessment: Don't play weak sets if opponents can Skout & Show easily
            if opp_ss_count > 0 and len(show["indices"]) < 3 and not is_endgame:
                score -= 5.0 * opp_ss_count
                
            if is_round_end_threat:
                score += 500.0 # Force a block
            
            # KILLER INSTINCT: Finishing bonus
            if len(dummy_hand) == 0:
                score += 1000.0 

            choices.append({**show, "score": score, "action": "show"})

        # 2. EVALUATE SKOUT
        if engine.current_trick.cards:
            skout_cards = engine.current_trick.cards
            # Optimization: only evaluate ends unless it's a set
            valid_indices = [0, len(skout_cards)-1]
            if SkoutRules.is_set(skout_cards): valid_indices = list(range(len(skout_cards)))
            
            for skout_idx in valid_indices:
                card_to_skout = skout_cards[skout_idx]
                for insert_at in range(len(hand_cards) + 1):
                    for flip in [False, True]:
                        new_c = card_to_skout.inverted() if flip else card_to_skout
                        temp_hand = hand_cards[:insert_at] + [new_c] + hand_cards[insert_at:]
                        
                        strength_gain = self.evaluate_hand_strength(temp_hand) - current_strength
                        potential_gain = self.evaluate_set_potential(temp_hand) - self.evaluate_set_potential(hand_cards)
                        
                        # Skout is an investment: pay now for future power
                        score = (strength_gain * w_delta) + (potential_gain * w_potential) - w_skout_cost
                        
                        # If we have too many cards, Skouting becomes less attractive
                        if hand_len >= 12: score -= 15.0
                        
                        # Penalty if Skouting hands the win to the owner
                        if is_round_end_threat:
                            score -= 400.0
                            
                        choices.append({"action": "skout", "skout_idx": skout_idx, "insert_at": insert_at, "flip": flip, "score": score})

        # 3. EVALUATE SKOUT & SHOW
        if player.skout_and_show_available and engine.current_trick.cards:
            skout_cards = engine.current_trick.cards
            valid_indices = [0, len(skout_cards)-1]
            if SkoutRules.is_set(skout_cards): valid_indices = list(range(len(skout_cards)))

            for skout_idx in valid_indices:
                for insert_at in range(len(hand_cards) + 1):
                    for flip in [False, True]:
                        new_c = skout_cards[skout_idx].inverted() if flip else skout_cards[skout_idx]
                        temp_h = hand_cards[:insert_at] + [new_c] + hand_cards[insert_at:]
                        
                        remaining_trick_cards = list(engine.current_trick.cards)
                        remaining_trick_cards.pop(skout_idx)
                        remaining_trick = Trick(remaining_trick_cards)
                        
                        shows = self.find_all_playable_groups(temp_h, remaining_trick)
                        if shows:
                            # S&S is the ultimate tempo move
                            best_s_item = max(shows, key=lambda x: x["power"])
                            dummy_h_post = [c for i, c in enumerate(temp_h) if i not in best_s_item["indices"]]
                            strength_loss = current_strength - self.evaluate_hand_strength(dummy_h_post)
                            
                            score = (len(best_s_item["indices"]) * 20.0 * panic_mult) - (strength_loss * w_delta)
                            score += (best_s_item["capture_count"] * w_capture * 6.0)
                            
                            # S&S should be saved unless it's very impactful or endgame
                            if not is_endgame and len(best_s_item["indices"]) < 3:
                                score -= 10.0

                            if len(dummy_h_post) == 0: score += 1200.0
                            
                            choices.append({
                                "action": "skout_and_show", "skout_idx": skout_idx, "insert_at": insert_at, "flip": flip,
                                "show_indices": best_s_item["indices"], "score": score 
                            })

        if not choices:
            if engine.current_trick.cards: 
                return {"action": "skout", "skout_idx": 0, "insert_at": 0, "flip": False, "reason": "Forced Skout"}
            return {"action": "show", "indices": [0], "reason": "Forced Show"}

        # BEHAVIORAL VARIANCE: Add small random noise to scores to avoid deterministic 'robotic' play
        # Higher difficulty = less noise (more optimal)
        noise_range = 1.0
        if self.difficulty == BotDifficulty.EASY: noise_range = 8.0
        elif self.difficulty == BotDifficulty.MIDDLE: noise_range = 4.0
        elif self.difficulty == BotDifficulty.HARD: noise_range = 1.5

        for c in choices:
            c["score"] += random.uniform(-noise_range, noise_range)

        best = max(choices, key=lambda x: x["score"])
        
        # LOGGING REASON
        final_reason = adaptive_reason
        if best["action"] == "skout_and_show": 
            final_reason = "S&S FATALITY" if len(best["show_indices"]) >= hand_len else "S&S COMBO"
        elif best["action"] == "show" and len(hand_cards) - len(best["indices"]) == 0:
            final_reason = "FINISHING MOVE"

        return {**best, "reason": final_reason}
        
    def make_move(self, engine: GameEngine) -> dict:
        """Executes the best chosen action on the engine and returns the action info."""
        action = self.choose_action(engine)
        if not action: return {}

        a_type = action.get("action")
        if a_type == "show":
            engine.play_cards(self.player_id, action["indices"])
        elif a_type == "skout":
            engine.skout(self.player_id, action["skout_idx"], action["insert_at"], action["flip"])
        elif a_type == "skout_and_show":
            engine.skout_and_show(self.player_id, action["skout_idx"], action["insert_at"], action["flip"], action["show_indices"])
        
        return action

    def evaluate_best_orientation(self, hand_cards: list[Card]) -> bool:
        strength_normal = self.evaluate_hand_strength(hand_cards)
        flipped_cards = [c.inverted() for c in hand_cards]
        strength_flipped = self.evaluate_hand_strength(flipped_cards)
        return strength_flipped > strength_normal

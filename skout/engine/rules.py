# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from typing import List, Optional
from ..core.card import Card

class SkoutRules:
    """
    Logic for validating plays and comparing trick strength in Skout.
    """
    
    @staticmethod
    def sort_if_sequence(cards: List[Card]) -> List[Card]:
        """
        Visually reorders a sequence to be strictly increasing (e.g., 6-5 -> 5-6).
        Does nothing if the group is a Set.
        """
        if not cards or len(cards) < 2:
            return cards
            
        values = [c.top_value for c in cards]
        is_set = all(v == values[0] for v in values)
        
        if not is_set:
            # If it's a sequence, we always return it in increasing order for UI consistency
            return sorted(cards, key=lambda c: c.top_value)
        return cards

    @staticmethod
    def is_set(cards: List[Card]) -> bool:
        if not cards: return False
        values = [c.top_value for c in cards]
        return all(v == values[0] for v in values)

    @staticmethod
    def is_valid_group(cards: List[Card]) -> bool:
        """
        A group must be either a 'Set' (all same value) 
        or a 'Sequence' (consecutive values).
        In Skout, sequences must be strictly increasing or decreasing.
        """
        if not cards:
            return False
        if len(cards) == 1:
            return True
        
        values = [c.top_value for c in cards]
        
        # Check for Set (Flush)
        if all(v == values[0] for v in values):
            return True
        
        # Check for Sequence (must be strictly increasing or strictly decreasing)
        # Increasing
        is_increasing = all(values[i] + 1 == values[i+1] for i in range(len(values) - 1))
        # Decreasing
        is_decreasing = all(values[i] - 1 == values[i+1] for i in range(len(values) - 1))
        
        return is_increasing or is_decreasing

    @staticmethod
    def get_power_level(cards: List[Card]) -> int:
        """
        Calculates a numeric power level for comparison.
        Skout Hierarchy:
        1. Number of cards (More is always better)
        2. Set vs Sequence (Set beats Sequence of same length)
        3. Higher minimum value in the group
        
        We can encode this as: (length * 1000) + (is_set * 100) + min_value
        """
        if not cards:
            return 0
            
        length = len(cards)
        values = [c.top_value for c in cards]
        is_set = all(v == values[0] for v in values)
        min_val = min(values)
        
        return (length * 1000) + (100 if is_set else 0) + min_val

    @staticmethod
    def get_readable_power(cards: List[Card]) -> str:
        """Returns a concise numeric representation with spaces (e.g., '10 10' or '9 10')."""
        if not cards: return ""
        
        # Visually normalize
        display_cards = SkoutRules.sort_if_sequence(cards)
        # Join values with spaces to prevent ambiguity with 10
        return " ".join(str(c.top_value) for c in display_cards)

    @staticmethod
    def beats(play: List[Card], current_trick: List[Card]) -> bool:
        """Determines if a new play beats the current trick on the table."""
        if not SkoutRules.is_valid_group(play):
            return False
            
        if not current_trick:
            return True # Any valid play beats an empty table
            
        return SkoutRules.get_power_level(play) > SkoutRules.get_power_level(current_trick)

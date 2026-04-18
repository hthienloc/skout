# SPDX-FileCopyrightText: 2026 Loc Huynh <huynhloc.contact@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass, field
from typing import List, Optional
from .card import Card

@dataclass
class Hand:
    """
    A player's hand. In Skout, cards cannot be reordered.
    The hand has an orientation determined at the start of the round.
    """
    cards: List[Card] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.cards)

    def get_card(self, index: int) -> Card:
        return self.cards[index]

    def remove_cards(self, indices: List[int]) -> List[Card]:
        """
        Removes cards at specified indices. 
        Indices are assumed to be sorted and valid.
        """
        removed = []
        # Remove in reverse order to maintain index validity
        for idx in sorted(indices, reverse=True):
            removed.append(self.cards.pop(idx))
        return removed[::-1] # Return in original relative order

    def insert_card(self, card: Card, index: int):
        """Inserts a card at a specific position (used during Skouting)."""
        self.cards.insert(index, card)

    def invert(self):
        """Inverts all cards in the hand while maintaining their relative positions."""
        self.cards = [c.inverted() for c in self.cards]

    def __repr__(self) -> str:
        return f"Hand({self.cards})"

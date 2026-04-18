# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from typing import List, Optional
from .card import Card

@dataclass
class Trick:
    """
    The set of cards currently on the table to be beaten.
    Owns the cards and tracks who played them.
    """
    cards: List[Card] = field(default_factory=list)
    player_id: Optional[str] = None

    def __len__(self) -> int:
        return len(self.cards)

    @property
    def top_values(self) -> List[int]:
        return [c.top_value for c in self.cards]

    def clear(self):
        self.cards = []
        self.player_id = None

    def __repr__(self) -> str:
        return f"Trick(by={self.player_id}, cards={self.cards})"

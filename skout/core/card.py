# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import NamedTuple

class CardValue(NamedTuple):
    top: int
    bottom: int

@dataclass(frozen=True)
class Card:
    """
    A Skout card has two numbers, one on the top and one on the bottom.
    The card can be held in its original orientation or inverted.
    """
    id: int
    values: CardValue
    is_inverted: bool = False

    @property
    def top_value(self) -> int:
        return self.values.bottom if self.is_inverted else self.values.top

    @property
    def bottom_value(self) -> int:
        return self.values.top if self.is_inverted else self.values.bottom

    def inverted(self) -> 'Card':
        """Returns a new Card instance with the opposite orientation."""
        return Card(id=self.id, values=self.values, is_inverted=not self.is_inverted)

    def __repr__(self) -> str:
        return f"Card({self.id}: {self.top_value}/{self.bottom_value})"

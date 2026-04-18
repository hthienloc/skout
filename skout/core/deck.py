# SPDX-FileCopyrightText: 2026 hthienloc
# SPDX-License-Identifier: MIT

import random
from typing import List
from .card import Card, CardValue

class Deck:
    """
    Handles card generation and shuffling for Skout.
    Skout (2019) has 45 cards (numbers 1-10, each pair appears once).
    Actually, combinations are unique.
    """
    @staticmethod
    def generate_skout_deck(player_count: int = 5) -> List[Card]:
        cards = []
        card_id = 0
        # Skout (2019) has 45 cards (unique combinations 1-10)
        for i in range(1, 11):
            for j in range(i + 1, 11):
                # Filter cards based on player count
                # 2p/4p: Remove 9/10 card
                if player_count in [2, 4] and i == 9 and j == 10:
                    continue
                # 3p: Remove any card containing a 10
                if player_count == 3 and (i == 10 or j == 10):
                    continue
                    
                # Randomize initial orientation
                is_inverted = random.choice([True, False])
                cards.append(Card(id=card_id, values=CardValue(top=i, bottom=j), is_inverted=is_inverted))
                card_id += 1
        return cards

    def __init__(self, player_count: int = 5):
        self.cards = self.generate_skout_deck(player_count)
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self, count: int) -> List[Card]:
        drawn = self.cards[:count]
        self.cards = self.cards[count:]
        return drawn

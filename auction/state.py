from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Optional, Literal, TypedDict, TYPE_CHECKING

from infra.logger import get_logger

if TYPE_CHECKING:
    from auction.models import BidRequest, StateResponse, ResultsResponse

# Phases of a round; engine advances in this order.
Phase = Literal["IDLE", "TURN_HUMAN", "TURN_AI1", "TURN_AI2", "TURN_AI3", "SETTLE"]


class HumanPendingBid(TypedDict):
    submit_id: str
    round_id: int
    turn_id: int
    amount: int


class AuctionState:
    """
    Central in-memory state for the auction.
    All read/write access to fields must occur under `self.lock` to ensure atomicity.
    """

    def __init__(self, *, rounds_total: int = 10, initial_budget: int = 1000) -> None:
        # Concurrency
        self.lock: asyncio.Lock = asyncio.Lock()
        self.logger = get_logger(__name__)

        # Configuration
        self.rounds_total: int = rounds_total
        self.initial_budget: int = initial_budget

        # Progress markers
        self.round_id: int = 0                 # 0 before start; 1..rounds_total during play
        self.turn_id: int = 0                  # 0..3 within a round (sequence index)
        self.phase: Phase = "IDLE"

        # Participants and public tallies
        self.sequence: list[str] = ["human", "ai1", "ai2", "ai3"]
        self.budgets: Dict[str, int] = {pid: initial_budget for pid in self.sequence}
        self.properties: Dict[str, int] = {pid: 0 for pid in self.sequence}

        # Per-round leader board
        self.current_high: int = 0
        self.current_winner: Optional[str] = None

        # Human submission buffer (read-and-clear each round/turn)
        self.human_pending_bid: Optional[HumanPendingBid] = None

        # Minimal in-memory event log (engine may append dict entries)
        self.history: list[dict] = []

        # Final results once the auction completes (None until finished)
        self.results: Optional["ResultsResponse"] = None

    async def reset(self) -> None:
        """Reset all mutable state to starting conditions before a new game."""
        async with self.lock:
            # Configuration-derived resets
            self.round_id = 0
            self.turn_id = 0
            self.phase = "IDLE"

            # Player ledgers
            self.budgets = {pid: self.initial_budget for pid in self.sequence}
            self.properties = {pid: 0 for pid in self.sequence}

            # Per-round fields
            self.current_high = 0
            self.current_winner = None
            self.human_pending_bid = None

            # Logs and terminal results
            self.history = []
            self.results = None

            self.logger.info("State reset: rounds_total=%d initial_budget=%d",
                             self.rounds_total, self.initial_budget)

    async def start_next_round(self) -> None:
        """Advance to the next round and clear per-round variables."""
        async with self.lock:
            next_round = self.round_id + 1
            if next_round > self.rounds_total:
                # Do not advance beyond configured total; engine should guard earlier.
                self.logger.warning("Attempt to start round %d beyond rounds_total=%d",
                                    next_round, self.rounds_total)
                return

            self.round_id = next_round
            self.turn_id = 0
            self.phase = "TURN_HUMAN"

            # Reset per-round leader board and any pending human input
            self.current_high = 0
            self.current_winner = None
            self.human_pending_bid = None

            self.logger.info("Round %d started", self.round_id)

    async def set_human_bid(self, bid: BidRequest) -> None:
        """Record the human player's submitted bid if valid for this turn."""
        ...

    async def apply_bid(self, player_id: str, amount: int) -> None:
        """Evaluate and apply a bid from any participant."""
        ...

    async def settle_round(self) -> None:
        """Award the current lot to the highest bidder and update balances."""
        ...

    async def snapshot(self) -> StateResponse:
        """Return a serializable snapshot of the current auction state."""
        ...

    async def finalize(self) -> ResultsResponse:
        """Compute and store the final auction results after all rounds complete."""
        ...

    async def log_event(self, event: dict) -> None:
        """Append a structured event to the in-memory history."""
        ...

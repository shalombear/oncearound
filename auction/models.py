from datetime import datetime
from typing import List, Dict, Optional

from pydantic import BaseModel, Field


class BidRequest(BaseModel):
    round_id: int = Field(gt=0)
    turn_id: int = Field(gt=0)
    amount: int = Field(ge=0)
    submit_id: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class StateResponse(BaseModel):
    round_id: int = Field(gt=0)
    turn_id: int = Field(ge=0)
    rounds_total: int = Field(gt=0)
    rounds_remaining: int = Field(ge=0)

    current_high: int = Field(ge=0)
    current_winner: Optional[str] = None

    sequence: List[str]
    budgets: Dict[str, int]
    properties: Dict[str, int]
    server_time: datetime

    model_config = {
        "extra": "forbid"
    }

    class ResultsResponse(BaseModel):
        winners_by_round: List[Dict[str, int]] = Field(default_factory=list)
        totals: Dict[str, Dict[str, int]]
        champion: str = Field(min_length=1)

        model_config = {
            "extra": "forbid"
        }
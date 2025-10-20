from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import asyncio

from auction.state import AuctionState
from auction.engine import AuctionEngine
from auction.models import BidRequest, StateResponse, ResultsResponse
from infra.logger import get_logger
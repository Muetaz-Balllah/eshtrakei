from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client
from backend.db import get_db
from backend.wallets.schemas import TopUpBody, WalletOut
from backend.wallets.services import top_up, view

router = APIRouter(tags=["wallet"])


@router.get("/api/wallet", response_model=WalletOut)
def read_wallet(principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return view(db, principal.user.id)


@router.post("/api/wallet/topups", response_model=WalletOut)
def add_funds(body: TopUpBody, principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return top_up(db, principal.user.id, body.amount, body.simulated_outcome)

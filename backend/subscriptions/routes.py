from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager
from backend.db import get_db
from backend.errors import AppError
from backend.subscriptions.schemas import ClientSubscriptions, PurchaseBody, PurchaseResult, RenewBody, SubscriptionOut
from backend.subscriptions.services import list_client_subscriptions, list_company_clients, purchase, renew

router = APIRouter(tags=["subscriptions"])


@router.post("/api/subscriptions/purchases", response_model=PurchaseResult)
def buy(body: PurchaseBody, principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return purchase(db, principal.user.id, body)


@router.get("/api/subscriptions", response_model=list[SubscriptionOut])
def my_subscriptions(principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_client_subscriptions(db, principal.user.id)


@router.post("/api/subscriptions/{subscription_id}/renew", response_model=PurchaseResult)
def client_renew(
    subscription_id: int,
    body: RenewBody,
    principal: Principal = Depends(require_client),
    db: Session = Depends(get_db),
):
    return renew(db, principal.user.id, subscription_id, body)


@router.get("/api/company/clients", response_model=list[ClientSubscriptions])
def company_clients(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return list_company_clients(db, principal.company_id)


@router.post("/api/company/subscriptions/{subscription_id}/renew", response_model=PurchaseResult)
def manager_renew(
    subscription_id: int,
    body: RenewBody,
    principal: Principal = Depends(require_company_manager),
    db: Session = Depends(get_db),
):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return renew(db, principal.user.id, subscription_id, body, company_id=principal.company_id)

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ComplaintCreate(BaseModel):
    kind: Literal["complaint", "technical_support"]
    target: Literal["company", "platform"]
    company_id: int | None = None
    message: str = Field(min_length=1)


class ReplyBody(BaseModel):
    message: str = Field(min_length=1)


class ComplaintOut(BaseModel):
    id: int
    kind: str
    target: str
    company_id: int | None
    company_name: str | None
    client_name: str
    client_phone: str | None
    message: str
    created_at: datetime
    reply_message: str | None
    replied_at: datetime | None

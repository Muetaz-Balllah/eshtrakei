from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    message: str
    kind: str
    is_read: bool
    created_at: datetime

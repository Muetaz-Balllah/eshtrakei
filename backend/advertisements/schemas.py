from pydantic import BaseModel


class AdvertisementPublic(BaseModel):
    id: int
    company_id: int
    company_name: str
    title: str
    body: str
    image_url: str | None

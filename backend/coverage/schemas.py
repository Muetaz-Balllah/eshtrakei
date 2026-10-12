from pydantic import BaseModel, Field


class TowerBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_meters: int = Field(gt=0, le=100000)


class TowerOut(BaseModel):
    id: int
    company_id: int
    company_name: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int
    is_active: bool

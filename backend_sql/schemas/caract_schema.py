from typing import Optional
from pydantic import BaseModel, ConfigDict


class CaractBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_accident: int
    jour: Optional[int] = None
    mois: Optional[int] = None
    an: Optional[str] = None
    hrmn: Optional[str] = None
    lum: Optional[int] = None
    dep: Optional[str] = None
    com: Optional[str] = None
    agg: Optional[int] = None
    int_: Optional[int] = None  # underscore to avoid Python keyword conflict
    atm: Optional[int] = None
    col: Optional[int] = None
    adr: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    date_ajout: str = None


class CaractCreate(CaractBase):
    pass


class CaractRead(CaractBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

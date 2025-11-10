from typing import Optional, Union
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ResultatAiBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sexe: int
    obsm: int
    pr: Union[str, int]
    jour: int
    col: int
    vma_cat: Optional[str] = None
    choc: int
    pr1: Union[str, int]
    mois: int
    age: int
    manv: int
    plan: int
    an: int
    cos_time: float
    n_passager: int
    motor: int
    larrout: int
    lum: int
    sin_time: float
    n_pieton: int
    catr: int
    surf: int
    dep: int
    senc: int
    circ: int
    infra: int
    agg: int
    day_of_week: int
    catv: int
    vosp: int
    situ: int
    int_: int
    obs: int
    prof: int
    atm: int
    is_holiday: int


class ResultatAiCreate(ResultatAiBase):
    gravite_estimee: Optional[int] = None


class ResultatAiRead(ResultatAiBase):
    id: int
    video_path: str
    date_ajout: datetime

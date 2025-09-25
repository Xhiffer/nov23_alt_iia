from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AITrainingModelDataBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_accident: int
    id_usager: Optional[int] = None
    id_vehicule: Optional[int] = None

    grav: Optional[int] = None
    sexe: Optional[int] = None
    an_nais: Optional[int] = None
    locp: Optional[int] = None
    n_passager: Optional[int] = None
    n_pieton: Optional[int] = None
    senc: Optional[int] = None
    catv: Optional[int] = None
    obs: Optional[int] = None
    obsm: Optional[int] = None
    choc: Optional[int] = None
    manv: Optional[int] = None
    motor: Optional[int] = None

    catr: Optional[int] = None
    circ: Optional[int] = None
    vosp: Optional[int] = None
    prof: Optional[int] = None
    pr: Optional[str] = None
    pr1: Optional[str] = None
    plan: Optional[int] = None
    larrout: Optional[int] = None
    surf: Optional[int] = None
    infra: Optional[int] = None
    situ: Optional[int] = None
    vma: Optional[int] = None

    jour: Optional[int] = None
    mois: Optional[int] = None
    an: Optional[int] = None
    lum: Optional[int] = None
    dep: Optional[str] = None
    agg: Optional[int] = None
    int_: Optional[int] = None  # avoid Python keyword
    atm: Optional[int] = None
    col: Optional[int] = None

    lat: Optional[float] = None
    long: Optional[float] = None
    hrmn_scaled: Optional[float] = None


class AITrainingModelDataCreate(AITrainingModelDataBase):
    pass


class AITrainingModelDataRead(AITrainingModelDataBase):
    id: int
    date_ajout: datetime

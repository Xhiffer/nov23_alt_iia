from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AccidentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Core identifiers
    id_accident: int
    id_usager: Optional[int] = None
    id_vehicule: Optional[int] = None

    # Usager info
    grav: Optional[int] = None
    sexe: Optional[int] = None
    an_nais: Optional[int] = None
    locp: Optional[int] = None
    n_passager: Optional[int] = None
    n_pieton: Optional[int] = None

    # Vehicle info
    senc: Optional[int] = None
    catv: Optional[int] = None
    obs: Optional[int] = None
    obsm: Optional[int] = None
    choc: Optional[int] = None
    manv: Optional[int] = None
    motor: Optional[int] = None

    # Lieu info
    catr: Optional[int] = None
    circ: Optional[int] = None
    vosp: Optional[int] = None
    prof: Optional[int] = None
    pr: Optional[str] = None
    pr1: Optional[str] = None
    plan: Optional[int] = None
    larrout: Optional[float] = None
    surf: Optional[int] = None
    infra: Optional[int] = None
    situ: Optional[int] = None
    vma: Optional[int] = None

    # Date & time info
    jour: Optional[int] = None
    mois: Optional[int] = None
    an: Optional[str] = None
    lum: Optional[int] = None
    dep: Optional[str] = None
    agg: Optional[int] = None
    int_: Optional[int] = None
    atm: Optional[int] = None
    col: Optional[int] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    hrmn_scaled: Optional[str] = None

class AccidentCreate(AccidentBase):
    pass

class AccidentRead(AccidentBase):
    id: int
    date_ajout: datetime

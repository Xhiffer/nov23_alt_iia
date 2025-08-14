from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UsagerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_accident: int
    id_usager: int  # corrigé
    id_vehicule: Optional[int] = None
    num_veh: Optional[str] = None
    place: int
    catu: int
    grav: int
    sexe: int
    an_nais: Optional[int] = None
    trajet: int

    secu1: Optional[int] = None
    secu2: Optional[int] = None
    secu3: Optional[int] = None

    locp: Optional[int] = None
    actp: Optional[str] = None  # corrigé
    etatp: Optional[int] = None


class UsagerCreate(UsagerBase):
    pass

class UsagerRead(UsagerBase):
    id: int
    date_ajout: datetime

from typing import Optional
from pydantic import BaseModel, ConfigDict

class UsagerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id_accident: int
    id_usager: int
    num_usager: Optional[int] = None
    place: int
    catu: int
    grav: int
    sexe: int
    trajet: int
    secu: Optional[int] = None
    locp: Optional[int] = None
    actp: Optional[int] = None
    etatp: Optional[int] = None

class UsagerCreate(UsagerBase):
    pass

class UsagerRead(UsagerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

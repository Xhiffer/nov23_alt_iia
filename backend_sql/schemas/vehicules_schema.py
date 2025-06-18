from typing import Optional

from pydantic import BaseModel, ConfigDict

class VehiculeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_accident: int
    id_vehicule: int
    num_veh: Optional[str] = None
    senc: int
    catv: int
    obs: int
    obsm: int
    choc: int
    manv: int
    motor: int
    occutc: Optional[int] = None

class VehiculeCreate(VehiculeBase):
    pass

class VehiculeRead(VehiculeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

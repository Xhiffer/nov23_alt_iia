from typing import Optional
from pydantic import BaseModel, ConfigDict

class ResultatAiBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre_vehicules: int
    vitesse_estimee: float
    impact_detecte: bool
    conditions_meteo: str
    presence_pietons: bool
    type_route: str

    # TODO: Ajouter ces champs si nécessaire plus tard
    # video: Optional[str] = None
    # gravites_tags: Optional[list[str]] = None

class ResultatAiCreate(ResultatAiBase):
    pass

class ResultatAiRead(ResultatAiBase):
    id: int

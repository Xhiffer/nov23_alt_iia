from typing import Optional
from pydantic import BaseModel, ConfigDict
from schemas.gravites_tags_schema import GraviteTagRead
class ResultatAiBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre_vehicules: int
    vitesse_estimee: float
    impact_detecte: bool
    conditions_meteo: str
    presence_pietons: bool
    type_route: str
    


class ResultatAiCreate(ResultatAiBase):
    gravite_estimee: Optional[str] = None

class ResultatAiRead(ResultatAiBase):
    id: int
    gravite_tag: Optional[GraviteTagRead] = None
    video_path: str

from typing import Optional
from pydantic import BaseModel, ConfigDict

class GraviteTagRead(BaseModel):
    id: int
    label: str
    color: str

    model_config = ConfigDict(from_attributes=True)
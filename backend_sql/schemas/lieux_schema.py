from typing import Optional
from pydantic import BaseModel, ConfigDict


class LieuBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_accident: int
    catr: int
    voie: Optional[str] = None
    v1: Optional[int] = None
    v2: Optional[str] = None
    circ: Optional[int] = None
    nbv: Optional[str] = None
    vosp: Optional[int] = None
    prof: Optional[int] = None
    pr: Optional[str] = None
    pr1: Optional[str] = None
    plan: Optional[int] = None
    lartpc: Optional[float] = None
    larrout: Optional[float] = None
    surf: Optional[int] = None
    infra: Optional[int] = None
    situ: Optional[int] = None
    vma: Optional[int] = None


class LieuCreate(LieuBase):
    pass


class LieuRead(LieuBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

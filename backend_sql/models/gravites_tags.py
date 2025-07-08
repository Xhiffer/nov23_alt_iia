from sqlalchemy import Column, Integer, String
from . import Base

class GraviteTag(Base):
    __tablename__ = "gravite_tag"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    label = Column(String, unique=True, nullable=False, comment="Gravité de l'accident")
    color = Column(String(7), nullable=False)

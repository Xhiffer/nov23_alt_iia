from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Caract(Base):
    __tablename__ = "caract"

    id_accident = Column(Integer, primary_key=True, index=True)
    jour = Column(Integer)
    mois = Column(Integer)
    an = Column(String, index=True)                    
    hrmn = Column(String)                              
    lum = Column(Integer)
    dep = Column(String)                              
    com = Column(String)                              
    agg = Column(Integer)
    int_ = Column(Integer)                             
    atm = Column(Integer)
    col = Column(Integer)
    adr = Column(String)                             
    lat = Column(Float)
    long = Column(Float)     
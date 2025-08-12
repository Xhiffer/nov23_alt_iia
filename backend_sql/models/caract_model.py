from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from datetime import datetime
from . import Base  # Assuming Base is imported correctly

class Caract(Base):
    __tablename__ = "caract"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    id_accident = Column(BigInteger, index=True) 
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

    date_ajout = Column(DateTime, default=datetime.now, nullable=False)

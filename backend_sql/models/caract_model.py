from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Caract(Base):
    __tablename__ = "caract"

    id_accident = Column(Integer, primary_key=True, index=True)
    jour = Column(Integer)
    mois = Column(Integer)
    an = Column(String, index=True)                    
    hrmn = Column(String)  #date de mise a jour de l'accident    
    lum = Column(Integer) #luminere
    dep = Column(String) #departement                   
    com = Column(String) # ??               
    agg = Column(Integer) # agglomération ->2 // hors agglomération ->1
    int_ = Column(Integer) #intersection                   
    atm = Column(Integer) #condition atmospherique
    col = Column(Integer) #type de collision
    adr = Column(String) #adresse            
    lat = Column(Float) #latitude
    long = Column(Float) #logitude
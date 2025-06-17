from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Vehicule(Base):
    __tablename__ = "vehicules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_accident = Column(Integer, index=True) #accident_id
    id_vehicule = Column(String, unique=True)
    num_veh = Column(String) #??? 
    senc = Column(Integer) #sens de circulation - OK
    catv = Column(Integer) #categorie véhicule - OK
    obs = Column(Integer)  # obsacle fixe heurte - OK
    obsm = Column(Integer) #obstacle mobile heurte - OK
    choc = Column(Integer) #point de choc initial - OK
    manv = Column(Integer) #manoeuvre principale avant accident - OK
    motor = Column(Integer) #type de motorisation - ok (mais je pense on le garde pas)
    occutc = Column(Integer) #Vide --> pas besoin 

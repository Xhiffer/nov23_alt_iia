from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base
from . import Base




class Vehicule(Base):
    __tablename__ = "vehicules"

    id = Column(Integer, primary_key=True, index=True)
    id_accident = Column(BigInteger, index=True)
    id_vehicule = Column(BigInteger, index=True)
    num_veh = Column(String) #??? 
    senc = Column(Integer) #sens de circulation - OK
    catv = Column(Integer) #categorie véhicule - OK
    obs = Column(Integer)  # obsacle fixe heurte - OK
    obsm = Column(Integer) #obstacle mobile heurte - OK
    choc = Column(Integer) #point de choc initial - OK
    manv = Column(Integer) #manoeuvre principale avant accident - OK
    motor = Column(Integer) #type de motorisation - ok (mais je pense on le garde pas)
    occutc = Column(Integer) #Vide --> pas besoin 

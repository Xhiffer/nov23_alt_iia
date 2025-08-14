from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Accident(Base):
    __tablename__ = "accidents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Core identifiers
    id_accident = Column(BigInteger, index=True)
    id_usager = Column(BigInteger, index=True)
    id_vehicule = Column(BigInteger, index=True)

    # Usager info
    grav = Column(Integer)       # gravity of injury
    sexe = Column(Integer)
    an_nais = Column(Integer)
    locp = Column(Integer)
    n_passager = Column(Integer)
    n_pieton = Column(Integer)

    # Vehicle info
    senc = Column(Integer)
    catv = Column(Integer)
    obs = Column(Integer)
    obsm = Column(Integer)
    choc = Column(Integer)
    manv = Column(Integer)
    motor = Column(Integer)

    # Lieu info
    catr = Column(Integer)
    circ = Column(Integer)
    vosp = Column(Integer)
    prof = Column(Integer)
    pr = Column(String)
    pr1 = Column(String)
    plan = Column(Integer)
    larrout = Column(Float)
    surf = Column(Integer)
    infra = Column(Integer)
    situ = Column(Integer)
    vma = Column(Integer)

    # Date & time info
    jour = Column(Integer)
    mois = Column(Integer)
    an = Column(String)
    lum = Column(Integer)
    dep = Column(String)
    agg = Column(Integer)
    int_ = Column(Integer)
    atm = Column(Integer)
    col = Column(Integer)
    lat = Column(Float)
    long = Column(Float)
    hrmn_scaled = Column(String)


    date_ajout = Column(DateTime, default=datetime.now, nullable=False)

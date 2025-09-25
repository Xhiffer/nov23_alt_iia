from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from datetime import datetime
from . import Base  # Assuming Base is imported correctly


class AITrainingModelData(Base):
    __tablename__ = "ai_training_model_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    id_accident = Column(BigInteger, index=True)
    id_usager = Column(BigInteger, index=True)
    id_vehicule = Column(BigInteger, index=True)

    grav = Column(Integer)       # gravité
    sexe = Column(Integer)       # sexe
    an_nais = Column(Integer)    # année de naissance
    locp = Column(Integer)       # localisation piéton
    n_passager = Column(Integer) # nombre passagers
    n_pieton = Column(Integer)   # nombre piétons
    senc = Column(Integer)       # sens de circulation
    catv = Column(Integer)       # catégorie véhicule
    obs = Column(Integer)        # obstacle fixe heurté
    obsm = Column(Integer)       # obstacle mobile heurté
    choc = Column(Integer)       # point de choc
    manv = Column(Integer)       # manœuvre
    motor = Column(Integer)      # motorisation

    catr = Column(Integer)       # catégorie route
    circ = Column(Integer)       # régime de circulation
    vosp = Column(Integer)       # voies spéciales
    prof = Column(Integer)       # profil en long
    pr = Column(String)          # point repère
    pr1 = Column(String)         # secondaire point repère
    plan = Column(Integer)       # tracé en plan
    larrout = Column(Integer)    # largeur route
    surf = Column(Integer)       # état de surface
    infra = Column(Integer)      # infrastructure
    situ = Column(Integer)       # situation
    vma = Column(Integer)        # vitesse max autorisée

    jour = Column(Integer)
    mois = Column(Integer)
    an = Column(Integer, index=True)
    lum = Column(Integer)
    dep = Column(String)
    agg = Column(Integer)
    int_ = Column(Integer)
    atm = Column(Integer)
    col = Column(Integer)

    lat = Column(Float)
    long = Column(Float)
    hrmn_scaled = Column(Float)

    date_ajout = Column(DateTime, default=datetime.now, nullable=False)

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from . import Base
from sqlalchemy.orm import relationship


class ResultatAi(Base):
    __tablename__ = "resultat_ai"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # --- Features used by the ML model ---
    sexe = Column(Integer, nullable=False)
    obsm = Column(Integer, nullable=False)
    pr = Column(String, nullable=False)
    jour = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    vma_cat = Column(String, nullable=True)
    choc = Column(Integer, nullable=False)
    pr1 = Column(String, nullable=False)
    mois = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    manv = Column(Integer, nullable=False)
    plan = Column(Integer, nullable=False)
    an = Column(Integer, nullable=False)
    cos_time = Column(Float, nullable=False)
    n_passager = Column(Integer, nullable=False)
    motor = Column(Integer, nullable=False)
    larrout = Column(Integer, nullable=False)
    lum = Column(Integer, nullable=False)
    sin_time = Column(Float, nullable=False)
    n_pieton = Column(Integer, nullable=False)
    catr = Column(Integer, nullable=False)
    surf = Column(Integer, nullable=False)
    dep = Column(Integer, nullable=False)
    senc = Column(Integer, nullable=False)
    circ = Column(Integer, nullable=False)
    infra = Column(Integer, nullable=False)
    agg = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    catv = Column(Integer, nullable=False)
    vosp = Column(Integer, nullable=False)
    situ = Column(Integer, nullable=False)
    int_ = Column(Integer, nullable=False)
    obs = Column(Integer, nullable=False)
    prof = Column(Integer, nullable=False)
    atm = Column(Integer, nullable=False)
    is_holiday = Column(Integer, nullable=False)

    # --- Metadata and relationships ---
    video_path = Column(String, nullable=True, comment="Chemin vers la vidéo de l'accident")

    gravite_tag_id = Column(Integer, ForeignKey("gravite_tag.id"), nullable=True)
    gravite_tag = relationship("GraviteTag", backref="accidents")

    date_ajout = Column(DateTime, default=datetime.now, nullable=False)

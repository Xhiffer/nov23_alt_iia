from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger,Boolean,ForeignKey
from datetime import datetime
from . import Base
from sqlalchemy.orm import relationship

class ResultatAi(Base):
    __tablename__ = "resultat_ai"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    nombre_vehicules = Column(Integer, nullable=False, comment="Nombre total de véhicules impliqués")
    vitesse_estimee = Column(Float, nullable=False, comment="Vitesse estimée au moment de l'accident (km/h)")
    impact_detecte = Column(Boolean, nullable=False, comment="Est-ce qu'un impact a été détecté ?")
    conditions_meteo = Column(String, nullable=False, comment="Conditions météorologiques au moment de l'accident")
    presence_pietons = Column(Boolean, nullable=False, comment="Y avait-il des piétons impliqués ?")
    type_route = Column(String, nullable=False, comment="Type de route (ex: autoroute, départementale, etc.)")
    video_path = Column(String, nullable=True, comment="Chemin vers la vidéo de l'accident")

    gravite_tag_id = Column(Integer, ForeignKey("gravite_tag.id"), nullable=True)
    gravite_tag = relationship("GraviteTag", backref="accidents")
    date_ajout = Column(DateTime, default=datetime.now, nullable=False)


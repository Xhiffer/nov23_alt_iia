from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base

from . import Base
"""
-1 == no data
"""
class Usager(Base):
    __tablename__ = "usagers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)



    id_accident = Column(BigInteger, index=True)  # accident_id
    id_usager = Column(String, index=True)  
    id_vehicule = Column(BigInteger, index=True) 
    num_veh = Column(String) # ?
    place = Column(Integer) #place dans le vehicule ?
    catu = Column(Integer) # categorie ? 1) conducteur, 2) passager 3) piéton
    grav = Column(Integer) # 1 indemn, 2 tué, 3 blessé, 4 blessé léger    
    sexe = Column(Integer) # 1 homme, 2 femme
    an_nais = Column(Integer)   #année de naissance             
    trajet = Column(Integer) # 1) domicile - travail, 2) domicile - école, 3) courses - achats, 4) utilisation prof., 5) promenade - loisir 9) autre
    #### equipement de securite 
    """
    0) aucun équipement
    1) cienture
    2) casque 
    3) dispositif enfant
    4) gilet réflechissant
    5) air bag (2/3RM)
    6) gants (2/3RM)
    7)gats+airbag(2/3RM)
    8) non déterminable 
    9) autre
    """
    secu1 = Column(Integer)
    secu2 = Column(Integer)
    secu3 = Column(Integer)
    ###########
    locp = Column(Integer) # localisation du pieton
    actp = Column(String) #activité du pieton
    etatp = Column(Integer) #etat du pieton 1 - seul 2- accompagné 3- en groupe

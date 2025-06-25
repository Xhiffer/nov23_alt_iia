from sqlalchemy import Column, Integer, String, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base

from . import Base


class Lieu(Base):
    __tablename__ = "lieux"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_accident = Column(BigInteger, index=True) 
 # num_acc
    catr = Column(Integer) #categorie
    voie = Column(String) #voie special ?
    ##### ca m'a l'air chiant a parser // utiliser franchement.  (bis// ter // etc) + A B C ..
    v1 = Column(Integer) ## flemme
    v2 = Column(String)  ## flemme 
    #####
    circ = Column(Integer) # regime de circulation ?
    nbv = Column(String) # nombre de voies de circulation ?
    vosp = Column(Integer) # voie speciale
    prof = Column(Integer)  # profile en long
    pr = Column(String) # point repere # je ne sais pas comment lire ca 
    pr1 = Column(String) # point repere # je ne sais pas comment lire ca 
    plan = Column(Integer) # Trace en plan 
    lartpc = Column(Float) # full nan 
    larrout = Column(Float) # trouve pas l'info dans pdf
    surf = Column(Integer) #etat surface ?
    infra = Column(Integer) #amenagement infrastructure
    situ = Column(Integer) #situation de l'accident
    vma = Column(Integer) #vitesse maximale autorisee ?
    
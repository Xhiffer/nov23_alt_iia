# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base 
import models.vehicules_model
import models.usagers_model
import models.caract_model
import models.lieux_model
# import models.gravites_tags
import models.resultat_ai_model
import models.ai_training_model_data_model

# Load environment variables from .env
load_dotenv()

# Environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "db")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Database connection URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# SQLAlchemy engine setup
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=1800
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




# Create all tables (checkfirst prevents dropping/recreating)
Base.metadata.create_all(bind=engine, checkfirst=True)

import sys
import os
sys.path.append("/app")

import pandas as pd
from sqlalchemy.orm import Session
from models.caract_model import Caract  # Assure-toi que ce chemin est correct
from database import SessionLocal
from dotenv import load_dotenv
import logging
from scripts.extensions_scripts import *  # check_lock_file, create_lock_file, remove_lock_file
from pandas import isna

# Setup
load_dotenv()
sys.path.append("/app")

# Logging
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_folder, 'import_caract.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def safe_float(value):
    if isna(value):
        return None
    try:
        return float(str(value).replace(',', '.'))
    except ValueError:
        return None

def import_caract():
    csv_file = 'scripts/csv/caract-2023.csv'
    logging.info(f"Reading CSV file: {csv_file}")

    try:
        df = pd.read_csv(csv_file, delimiter=';')
        db = next(get_db())
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return

    for index, row in df.iterrows():
        try:
            caract = Caract(
                id_accident = int(row.get('Num_Acc')) if not isna(row.get('Num_Acc')) else None,
                jour = None if isna(row.get('jour')) else int(row.get('jour')),
                mois = None if isna(row.get('mois')) else int(row.get('mois')),
                an = None if isna(row.get('an')) else str(row.get('an')),
                hrmn = None if isna(row.get('hrmn')) else str(row.get('hrmn')),
                lum = None if isna(row.get('lum')) else int(row.get('lum')),
                dep = None if isna(row.get('dep')) else str(row.get('dep')),
                com = None if isna(row.get('com')) else str(row.get('com')),
                agg = None if isna(row.get('agg')) else int(row.get('agg')),
                int_ = None if isna(row.get('int')) else int(row.get('int')),
                atm = None if isna(row.get('atm')) else int(row.get('atm')),
                col = None if isna(row.get('col')) else int(row.get('col')),
                adr = None if isna(row.get('adr')) else str(row.get('adr')),
                lat = safe_float(row.get('lat')),
                long = safe_float(row.get('long')),
            )
            db.add(caract)
            db.commit()
        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            db.rollback()
            continue

    try:
        db.commit()
        logging.info("All caract rows have been successfully committed to the database.")
    except Exception as e:
        logging.error(f"Error committing to the database: {e}")
        db.rollback()

if __name__ == "__main__":
    LOCK_FILE = "scripts/import_caract.lock"
    if check_lock_file(LOCK_FILE):
        print("Another instance is already running. Exiting.")
    else:
        try:
            logging.info("Caract import process started.")
            print("Caract import process started...")
            create_lock_file(LOCK_FILE, sys.argv)
            import_caract()
            logging.info("Caract import process finished.")
            print("Caract data imported successfully!")
        finally:
            remove_lock_file(LOCK_FILE)

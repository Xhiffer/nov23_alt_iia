import sys
import os

# Adjust the Python path to include the application root directory
sys.path.append("/app")

import pandas as pd
from sqlalchemy.orm import Session
from models.vehicules_model import Vehicule  # changed import
from database import SessionLocal
from dotenv import load_dotenv
import logging
from scripts.extensions_scripts import *  # assuming your helper funcs are here
from pandas import isna

load_dotenv()

# Setup logging folder and file
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'import_vehicules.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# DB session generator (same as before)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def import_vehicules():
    csv_file = 'scripts/csv/vehicules-2023.csv'
    logging.info(f"Reading CSV file: {csv_file}")

    try:
        df = pd.read_csv(csv_file, delimiter=';')
        df['id_vehicule'] = df['id_vehicule'].astype(str).str.replace('\xa0', '').str.replace(' ', '')
        db = next(get_db())
    except Exception as e:
        logging.error(f"Error reading the CSV file: {e}")
        return

    for index, row in df.iterrows():

        try:
            vehicule = Vehicule(
                id_accident = int(row.get('Num_Acc')) if row.get('Num_Acc') is not None else None,
                id_vehicule = int(str(row.get('id_vehicule')).replace('\xa0', '').replace(' ', '')) if row.get('id_vehicule') else None,
                num_veh = row.get('num_veh'),
                senc = row.get('senc'),
                catv = row.get('catv'),
                obs = row.get('obs'),
                obsm = row.get('obsm'),
                choc = row.get('choc'),
                manv = row.get('manv'),
                motor = row.get('motor'),
                occutc = None if isna(row.get('occutc')) else int(row.get('occutc')),

            )
            db.add(vehicule)
            db.commit()
        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            db.rollback()
            continue

    try:
        db.commit()
        logging.info("All vehicules have been successfully committed to the database.")
    except Exception as e:
        logging.error(f"Error committing to the database: {e}")
        db.rollback()


if __name__ == "__main__":
    LOCK_FILE = "scripts/import_vehicules.lock"
    if check_lock_file(LOCK_FILE):
        print("Another instance is already running. Exiting.")
    else:
        try:
            logging.info("Vehicules import process started.")
            print("Vehicules import process started...")
            create_lock_file(LOCK_FILE, sys.argv)
            import_vehicules()
            logging.info("Vehicules import process finished.")
            print("Vehicules have been imported successfully!")
        finally:
            remove_lock_file(LOCK_FILE)

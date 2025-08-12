import sys
import os
# Adjust the Python path to include the application root directory
sys.path.append("/app")
import pandas as pd

from sqlalchemy.orm import Session
from database import SessionLocal
from models.usagers_model import Usager  # Adjust path as needed
from dotenv import load_dotenv
import logging
from pandas import isna
from scripts.extensions_scripts import check_lock_file, create_lock_file, remove_lock_file

# Setup
load_dotenv()

log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'import_usagers.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def import_usagers():
    csv_file = 'scripts/csv/usagers-2023.csv'
    logging.info(f"Reading CSV file: {csv_file}")

    try:
        df = pd.read_csv(csv_file, delimiter=';')
        df['id_usager'] = df['id_usager'].astype(str).str.replace('\xa0', '').str.replace(' ', '')
        df['id_vehicule'] = df['id_vehicule'].astype(str).str.replace('\xa0', '').str.replace(' ', '')
        db = next(get_db())
    except Exception as e:
        logging.error(f"Error reading the CSV file: {e}")
        return

    for index, row in df.iterrows():
        try:
            usager = Usager(
                id_accident=int(row.get('Num_Acc')) if not isna(row.get('Num_Acc')) else None,
                id_usager=str(row.get('id_usager')),
                id_vehicule=str(row.get('id_vehicule')),
                num_veh=row.get('num_veh'),
                place=None if isna(row.get('place')) else int(row.get('place')),
                catu=None if isna(row.get('catu')) else int(row.get('catu')),
                grav=None if isna(row.get('grav')) else int(row.get('grav')),
                sexe=None if isna(row.get('sexe')) else int(row.get('sexe')),
                an_nais=None if isna(row.get('an_nais')) else int(row.get('an_nais')),
                trajet=None if isna(row.get('trajet')) else int(row.get('trajet')),
                secu1=None if isna(row.get('secu1')) else int(row.get('secu1')),
                secu2=None if isna(row.get('secu2')) else int(row.get('secu2')),
                secu3=None if isna(row.get('secu3')) else int(row.get('secu3')),
                locp=None if isna(row.get('locp')) else int(row.get('locp')),
                actp=row.get('actp'),
                etatp=None if isna(row.get('etatp')) else int(row.get('etatp')),
                date_ajout = pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S'),

            )
            db.add(usager)
            db.commit()
        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            db.rollback()
            continue

    try:
        db.commit()
        logging.info("All usagers have been successfully committed to the database.")
    except Exception as e:
        logging.error(f"Error committing to the database: {e}")
        db.rollback()

if __name__ == "__main__":
    LOCK_FILE = "scripts/import_usagers.lock"
    if check_lock_file(LOCK_FILE):
        print("Another instance is already running. Exiting.")
    else:
        try:
            logging.info("Usagers import process started.")
            print("Usagers import process started...")
            create_lock_file(LOCK_FILE, sys.argv)
            import_usagers()
            logging.info("Usagers import process finished.")
            print("Usagers have been imported successfully!")
        finally:
            remove_lock_file(LOCK_FILE)

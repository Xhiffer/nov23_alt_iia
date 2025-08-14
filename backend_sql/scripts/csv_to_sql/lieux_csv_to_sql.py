import sys
import os
sys.path.append("/app")
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from models.lieux_model import Lieu
from dotenv import load_dotenv
import logging
from pandas import isna
from scripts.extensions_scripts import check_lock_file, create_lock_file, remove_lock_file

# Setup
load_dotenv()

log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'import_lieux.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def import_lieux():
    csv_file = 'scripts/csv/lieux-2023.csv'
    logging.info(f"Reading CSV file: {csv_file}")

    try:
        df = pd.read_csv(csv_file, delimiter=';')
        db = next(get_db())
    except Exception as e:
        logging.error(f"Error reading the CSV file: {e}")
        return

    for index, row in df.iterrows():
        try:
            lieu = Lieu(
                id_accident=int(row.get('Num_Acc')) if not isna(row.get('Num_Acc')) else None,
                catr=None if isna(row.get('catr')) else int(row.get('catr')),
                voie=None if isna(row.get('voie')) else str(row.get('voie')),
                v1=None if isna(row.get('v1')) else int(row.get('v1')),
                v2=None if isna(row.get('v2')) else str(row.get('v2')),
                circ=None if isna(row.get('circ')) else int(row.get('circ')),
                nbv=None if isna(row.get('nbv')) else str(row.get('nbv')),
                vosp=None if isna(row.get('vosp')) else int(row.get('vosp')),
                prof=None if isna(row.get('prof')) else int(row.get('prof')),
                pr=None if isna(row.get('pr')) else str(row.get('pr')),
                pr1=None if isna(row.get('pr1')) else str(row.get('pr1')),
                plan=None if isna(row.get('plan')) else int(row.get('plan')),
                lartpc=None if isna(row.get('lartpc')) else float(str(row.get('lartpc')).replace(',', '.')),
                larrout=None if isna(row.get('larrout')) else float(str(row.get('larrout')).replace(',', '.')),
                surf=None if isna(row.get('surf')) else int(row.get('surf')),
                infra=None if isna(row.get('infra')) else int(row.get('infra')),
                situ=None if isna(row.get('situ')) else int(row.get('situ')),
                vma=None if isna(row.get('vma')) else int(row.get('vma')),


            )
            db.add(lieu)
            db.commit()
        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            db.rollback()
            continue

    try:
        db.commit()
        logging.info("All lieux have been successfully committed to the database.")
    except Exception as e:
        logging.error(f"Error committing to the database: {e}")
        db.rollback()

if __name__ == "__main__":
    LOCK_FILE = "scripts/import_lieux.lock"
    if check_lock_file(LOCK_FILE):
        print("Another instance is already running. Exiting.")
    else:
        try:
            logging.info("Lieux import process started.")
            print("Lieux import process started...")
            create_lock_file(LOCK_FILE, sys.argv)
            import_lieux()
            logging.info("Lieux import process finished.")
            print("Lieux have been imported successfully!")
        finally:
            remove_lock_file(LOCK_FILE)

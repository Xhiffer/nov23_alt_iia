import sys
import os

# Adjust the Python path to include the application root directory
sys.path.append("/app")

import pandas as pd
from sqlalchemy.orm import Session
from models.livres import Livre
from database import SessionLocal
from dotenv import load_dotenv
import logging
from datetime import datetime
from scripts.extensions_scripts import *
# Load environment variables (optional, in case you want to use them in the script)
load_dotenv()

# Set up logging
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'import_livres.log'),
    level=logging.INFO,  # Log all INFO level messages and higher
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create a new session to interact with the database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define function to add livres to the database
def import_livres():
    # Read the CSV file using pandas
    csv_file = 'scripts/data.csv'  # Change this to the path of your CSV file
    logging.info(f"Reading CSV file: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file)
        logging.info(f"CSV file {csv_file} loaded successfully.")
    except Exception as e:
        logging.error(f"Error reading the CSV file: {e}")
        return

    db = next(get_db())
    last_id = db.query(Livre.id).order_by(Livre.id.desc()).first()

    # If there's no Livre yet, start from 0
    start_id = last_id[0] if last_id else 0

    for index, row in df.iterrows():
        try:
            # Create a new Livre instance from each row
            if index + 1 > start_id:
                first_cover = row['covers'].split(',')[0] if row['covers'] else None
                livre = Livre(
                    covers=row['covers'],
                    first_cover=int(first_cover),
                    title=row['title'],
                    name=row['name'],
                    subjects=row['subjects'],
                    publish_year=row['publish_date'],
                    publishers=row['publishers'],
                    isbn_10=row['isbn_10'],
                    isbn_13=row['isbn_13'],
                    key_works=row['key_works'],
                    key_author=row['key_author'],
                    image_path="default_image_path"  # Set default image path or add logic for image paths
                )

                # Add the Livre object to the session
                db.add(livre)
                db.commit()

        
        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            continue

    # Commit remaining changes (in case there are fewer than `batch_size` rows left)
    try:
        db.commit()
        logging.info("All livres have been successfully committed to the database.")
    except Exception as e:
        logging.error(f"Error committing to the database: {e}")
        db.rollback()

if __name__ == "__main__":
    LOCK_FILE = "scripts/import_csv.lock"
    # Check if the lock file exists
    if check_lock_file(LOCK_FILE):
        print("Another instance is already running. Exiting.")
    else:
        try:
            logging.info("Livres import process started.")
            print("Livres import process started...")
            create_lock_file(LOCK_FILE, sys.argv)
            import_livres()
            logging.info("Livres import process finished.")
            print("Livres have been imported successfully!")
        finally:
            remove_lock_file(LOCK_FILE)
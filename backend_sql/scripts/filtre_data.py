

import requests
from typing import List, Dict, Union

from tomlkit import datetime

def fetch_api_data(base_url: str, table_name: str) -> Union[List[Dict], None]:
    """
    Fetches data from a FastAPI endpoint like http://localhost:8000/{table_name}

    Args:
        base_url (str): Base URL of the API, e.g., "http://localhost:8000"
        table_name (str): The name of the endpoint table, e.g., "caracts"

    Returns:
        List of dicts if successful, None otherwise
    """
    url = f"{base_url.rstrip('/')}/{table_name.lstrip('/')}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching {table_name} from {url}: {e}")
        return None




import unicodedata

def remove_accents(text):
    if isinstance(text, str):
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
        return text
    return text



import pandas as pd

base_url = "http://localhost:8000"
table_name = "caracts"

data = fetch_api_data(base_url, table_name)

if data:
    df_caract = pd.DataFrame(data)
    df_caract.head()  # Print just the first few rows
else:
    print("No data found.")

# df_caract.dropna(subset=['adr'], inplace=True) just pas uen variable utilisable.
df_caract.reset_index(drop=True, inplace=True)
df_caract.drop(columns=["id"], inplace=True)
df_caract.drop(columns=['adr'], inplace=True)
df_caract.drop(columns=["com"], inplace=True)



for col in df_caract.select_dtypes(include='object'):
    df_caract[col] = df_caract[col].str.strip()



def time_to_fraction(time_str):
    try:
        hours, minutes = map(int, time_str.split(":"))
        total_minutes = hours * 60 + minutes
        return total_minutes / (24 * 60)  # Normalize to [0,1]
    except:
        return None  # or np.nan

# Apply to your DataFrame
df_caract["hrmn_scaled"] = df_caract["hrmn"].apply(time_to_fraction)
df_caract.drop(columns=['hrmn'], inplace=True)

df_caract["dep"].nunique()



import pandas as pd

base_url = "http://localhost:8000"
table_name = "lieux"

data = fetch_api_data(base_url, table_name)

if data:
    df_lieux = pd.DataFrame(data)
    df_lieux.head()  # Print just the first few rows
else:
    print("No data found.")

for col in df_lieux.select_dtypes(include='object'):
    df_lieux[col] = df_lieux[col].str.strip().str.lower().apply(remove_accents)
df_lieux.drop(columns=['voie'], inplace=True)
df_lieux.drop(columns=['v1'], inplace=True)
df_lieux.drop(columns=['v2'], inplace=True)
df_lieux.drop(columns=['id'], inplace=True)
# trop d'options différentes pour cette variable je ne sais pas la quel traiter.
df_lieux.drop(columns=['nbv'], inplace=True)


df_lieux.drop(columns=['lartpc'], inplace=True)




import pandas as pd

base_url = "http://localhost:8000"
table_name = "usagers"

data = fetch_api_data(base_url, table_name)

if data:
    df_usagers = pd.DataFrame(data)
    df_usagers.head()  # Print just the first few rows
else:
    print("No data found.")

df_usagers.dropna(subset=['an_nais'], inplace=True)
df_usagers.reset_index(drop=True, inplace=True)
for col in df_usagers.select_dtypes(include='object'):
    df_usagers[col] = df_usagers[col].str.strip()

df_usagers.drop(columns=['id'], inplace=True)

#Je ne sais pas ce que c'est 
df_usagers.drop(columns=['num_veh'], inplace=True)  
df_usagers.drop(columns=['catu'], inplace=True)  # redondance trop grosse avec la colonne place 

#je supose que c'est pas des information visibles 
df_usagers.drop(columns=['secu1'], inplace=True)
df_usagers.drop(columns=['secu2'], inplace=True)
df_usagers.drop(columns=['secu3'], inplace=True)
#de même je ne sais pas l'état de la personne, ni le trajet
df_usagers.drop(columns=['etatp'], inplace=True)
df_usagers.drop(columns=['trajet'], inplace=True)
#posssible en soit d'avoir un model qui d'étermine l'action de la personne, mais pas dans notre cas
df_usagers.drop(columns=['actp'], inplace=True) 

#location du piétion (= place 10 je suppose)



import pandas as pd

# Count passengers (place 2 to 9) per accident
passagers_counts = df_usagers[df_usagers["place"].between(2, 9)].groupby("id_accident").size().rename("n_passager")

# Count pedestrians (place == 10) per accident
pieton_counts = df_usagers[df_usagers["place"] == 10].groupby("id_accident").size().rename("n_pieton")

# Filter only conducteurs (place == 1)
df_conducteurs = df_usagers[df_usagers["place"] == 1].copy()

# Merge both counts into the conducteur dataframe
df_conducteurs = df_conducteurs.merge(passagers_counts, on="id_accident", how="left")
df_conducteurs = df_conducteurs.merge(pieton_counts, on="id_accident", how="left")

# Fill NaN with 0
df_conducteurs["n_passager"] = df_conducteurs["n_passager"].fillna(0).astype(int)
df_conducteurs["n_pieton"] = df_conducteurs["n_pieton"].fillna(0).astype(int)

df_conducteurs = df_conducteurs[df_conducteurs["n_pieton"] <= 1]


# Step 1: Filter df_conducteurs where there's exactly 1 pedestrian
mask_pieton_1 = df_conducteurs["n_pieton"] == 1
df_with_1_pieton = df_conducteurs[mask_pieton_1].copy()

# Step 2: For each of those rows, replace locp with that of the pedestrian in df_usagers
for idx, row in df_with_1_pieton.iterrows():
    accident_id = row["id_accident"]

    # Get the corresponding pedestrian (place == 10) from df_usagers
    pieton_row = df_usagers[(df_usagers["id_accident"] == accident_id) & (df_usagers["place"] == 10)]

    if not pieton_row.empty:
        # If there's a pedestrian, get their locp
        pieton_locp = pieton_row.iloc[0]["locp"]

        # Replace driver's locp with the pedestrian's locp
        df_conducteurs.loc[idx, "locp"] = pieton_locp



# Replace all locp values of -1 with 0
df_conducteurs["locp"] = df_conducteurs["locp"].replace(-1, 0)

# Drop the 'place' column
df_conducteurs.drop(columns=["place"], inplace=True)

# Reset the index
df_conducteurs.reset_index(drop=True, inplace=True)




import pandas as pd

base_url = "http://localhost:8000"
table_name = "vehicules"

data = fetch_api_data(base_url, table_name)

if data:
    df_vehicules = pd.DataFrame(data)
    df_vehicules.head()  # Print just the first few rows
else:
    print("No data found.")


for col in df_vehicules.select_dtypes(include='object'):
    df_vehicules[col] = df_vehicules[col].str.strip()
df_vehicules.drop(columns=['occutc'], inplace=True)
df_vehicules.drop(columns=['num_veh'], inplace=True)
df_vehicules.drop(columns=['id'], inplace=True)




dfs = {
    'df_caract': df_caract,
    'df_lieux': df_lieux,
    'df_vehicules': df_vehicules,
    'df_conducteurs': df_conducteurs
}

for name, df in dfs.items():
    total_rows = len(df)
    duplicate_rows = df.duplicated(keep=False).sum()
    print(f"{name}:")
    print(f"  Total rows: {total_rows}")
    print(f"  Fully duplicated rows: {duplicate_rows}\n")



df_lieux_duplicates = df_lieux.drop_duplicates().reset_index(drop=True)



dfs = {
    'df_caract': df_caract,
    'df_lieux_duplicates': df_lieux_duplicates,
    'df_vehicules': df_vehicules,
    'df_conducteurs': df_conducteurs
}

for name, df in dfs.items():
    total_rows = len(df)
    duplicate_rows = df.duplicated(keep=False).sum()
    
    # Count how many accident IDs appear more than once
    accident_counts = df['id_accident'].value_counts()
    duplicated_accidents = accident_counts[accident_counts > 1]
    num_duplicated_accidents = len(duplicated_accidents)
    



######à voir :

# Filter only duplicated rows (based on 'id_accident')
# dups = df_lieux_duplicates[df_lieux_duplicates.duplicated(subset='id_accident', keep=False)]

# # Group by 'id_accident' to work on each group of duplicates
# def merge_duplicates(group):
#     # Replace -1 or 0 by the non (-1 or 0) value from the same group
#     for col in group.columns:
#         if col == 'id_accident':
#             continue
#         values = group[col].values
#         valid = [v for v in values if v not in [-1, 0]]
#         if valid:
#             group[col] = [v if v not in [-1, 0] else valid[0] for v in values]
#     return group

# # Apply the merging logic
# dups_fixed = dups.groupby('id_accident', group_keys=False).apply(merge_duplicates)

# # Update the original DataFrame with the corrected values
# df_lieux_duplicates.update(dups_fixed)
df_lieux_duplicates = df_lieux_duplicates.drop_duplicates(subset='id_accident', keep=False)



df_lieux_duplicates = df_lieux_duplicates.drop_duplicates().reset_index(drop=True)



dfs = {
    'df_caract': df_caract,
    'df_lieux_duplicates': df_lieux_duplicates,
    'df_vehicules': df_vehicules,
    'df_conducteurs': df_conducteurs
}

for name, df in dfs.items():
    total_rows = len(df)
    duplicate_rows = df.duplicated(keep=False).sum()
    
    # Count how many accident IDs appear more than once
    accident_counts = df['id_accident'].value_counts()
    duplicated_accidents = accident_counts[accident_counts > 1]
    num_duplicated_accidents = len(duplicated_accidents)




# Drop date_ajout from all DataFrames if it exists
for df in [df_conducteurs, df_vehicules, df_lieux_duplicates, df_caract]:
    if 'date_ajout' in df.columns:
        df.drop(columns=['date_ajout'], inplace=True)

# Merge all together on relevant keys
merged_df = pd.merge(
    df_conducteurs,
    df_vehicules,
    on=['id_vehicule', 'id_accident'],  # merge on both keys to avoid _x/_y
    how='inner'
)
merged_df = pd.merge(merged_df, df_lieux_duplicates, on='id_accident', how='inner')
merged_df = pd.merge(merged_df, df_caract, on='id_accident', how='inner')





import sys
import os
import logging
import pandas as pd
from sqlalchemy.orm import Session
from pandas import isna

# Project imports
sys.path.append("/app")
from database import SessionLocal
from models.ai_training_model_data_model import AITrainingModelData  # adjust path
from scripts.extensions_scripts import check_lock_file, create_lock_file, remove_lock_file

# Logging setup
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'import_ai_training_data.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def import_ai_training_data():
    try:
        df = merged_df
        db = next(get_db())
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return
    for index, row in df.iterrows():
        try:
            record = AITrainingModelData(
                id_accident=int(row.get('id_accident')) if not isna(row.get('id_accident')) else None,
                id_usager=None if isna(row.get('id_usager')) else int(row.get('id_usager')),
                id_vehicule=None if isna(row.get('id_vehicule')) else int(row.get('id_vehicule')),

                grav=None if isna(row.get('grav')) else int(row.get('grav')),
                sexe=None if isna(row.get('sexe')) else int(row.get('sexe')),
                an_nais=None if isna(row.get('an_nais')) else int(row.get('an_nais')),
                locp=None if isna(row.get('locp')) else int(row.get('locp')),
                n_passager=None if isna(row.get('n_passager')) else int(row.get('n_passager')),
                n_pieton=None if isna(row.get('n_pieton')) else int(row.get('n_pieton')),
                senc=None if isna(row.get('senc')) else int(row.get('senc')),
                catv=None if isna(row.get('catv')) else int(row.get('catv')),
                obs=None if isna(row.get('obs')) else int(row.get('obs')),
                obsm=None if isna(row.get('obsm')) else int(row.get('obsm')),
                choc=None if isna(row.get('choc')) else int(row.get('choc')),
                manv=None if isna(row.get('manv')) else int(row.get('manv')),
                motor=None if isna(row.get('motor')) else int(row.get('motor')),

                catr=None if isna(row.get('catr')) else int(row.get('catr')),
                circ=None if isna(row.get('circ')) else int(row.get('circ')),
                vosp=None if isna(row.get('vosp')) else int(row.get('vosp')),
                prof=None if isna(row.get('prof')) else int(row.get('prof')),
                pr=None if isna(row.get('pr')) else str(row.get('pr')),
                pr1=None if isna(row.get('pr1')) else str(row.get('pr1')),
                plan=None if isna(row.get('plan')) else int(row.get('plan')),
                larrout=None if isna(row.get('larrout')) else int(row.get('larrout')),
                surf=None if isna(row.get('surf')) else int(row.get('surf')),
                infra=None if isna(row.get('infra')) else int(row.get('infra')),
                situ=None if isna(row.get('situ')) else int(row.get('situ')),
                vma=None if isna(row.get('vma')) else int(row.get('vma')),
                jour=None if isna(row.get('jour')) else int(row.get('jour')),
                mois=None if isna(row.get('mois')) else int(row.get('mois')),
                an=None if isna(row.get('an')) else int(row.get('an')),
                lum=None if isna(row.get('lum')) else int(row.get('lum')),
                dep=None if isna(row.get('dep')) else str(row.get('dep')),
                agg=None if isna(row.get('agg')) else int(row.get('agg')),
                int_=None if isna(row.get('int_')) else int(row.get('int_')),
                atm=None if isna(row.get('atm')) else int(row.get('atm')),
                col=None if isna(row.get('col')) else int(row.get('col')),
                lat=None if isna(row.get('lat')) else float(row.get('lat')),
                long=None if isna(row.get('long')) else float(row.get('long')),
                hrmn_scaled=None if isna(row.get('hrmn_scaled')) else float(row.get('hrmn_scaled')),
                date_ajout=datetime.now()
            )

            db.add(record)
            db.commit()
        except Exception as e:
            logging.error(f"Error processing row {index}: {e}")
            db.rollback()
            continue

    try:
        db.commit()
        logging.info("All AI training data successfully committed.")
    except Exception as e:
        logging.error(f"Error committing final batch: {e}")
        db.rollback()

if __name__ == "__main__":
    LOCK_FILE = "scripts/import_ai_training_data.lock"
    if check_lock_file(LOCK_FILE):
        print("Another instance is already running. Exiting.")
    else:
        try:
            logging.info("AI Training Data import started.")
            print("AI Training Data import started...")
            create_lock_file(LOCK_FILE, sys.argv)
            import_ai_training_data()
            logging.info("AI Training Data import finished.")
            print("AI Training Data imported successfully!")
        finally:
            remove_lock_file(LOCK_FILE)

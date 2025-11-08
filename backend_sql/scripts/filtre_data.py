

import sys
import os
import traceback
import logging
import numpy as np
# Logging setup
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'import_ai_training_data.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
try:
    ##


    # Project imports
    sys.path.append("/app")

    from typing import List, Dict, Union
    import unicodedata
    import pandas as pd
    from datetime import datetime
    from sqlalchemy.orm import Session
    from pandas import isna
    from database import SessionLocal
    from models.ai_training_model_data_model import AITrainingModelData  # adjust path
    from routers.caract_router import get_all_caracts
    from routers.lieux_router import get_all_lieux
    from routers.usagers_router import get_all_usagers
    from routers.vehicules_router import get_all_vehicules
    from scripts.extensions_scripts import check_lock_file, create_lock_file, remove_lock_file
    import time

    ##

    db = SessionLocal()


    def remove_accents(text):
        if isinstance(text, str):
            text = unicodedata.normalize('NFD', text)
            text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
            return text
        return text


    # data = fetch_api_data(base_url, table_name)
    data = get_all_caracts(db)
    if data:
        rows = [obj.__dict__ for obj in data]
        df_caract = pd.DataFrame(rows)

    else:
        logging.info("No data found.")

    # df_caract.dropna(subset=['adr'], inplace=True) just pas uen variable utilisable.
    df_caract.reset_index(drop=True, inplace=True)
    df_caract.drop(columns=["id"], inplace=True, errors="ignore")
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





    data = get_all_lieux(db)

    if data:
        rows = [obj.__dict__ for obj in data]
        df_lieux = pd.DataFrame(rows)
    else:
        print("No data found.")

    for col in df_lieux.select_dtypes(include='object'):
        df_lieux[col] = df_lieux[col].astype(str).str.strip().str.lower().apply(remove_accents)

    df_lieux.drop(columns=['voie'], inplace=True)
    df_lieux.drop(columns=['v1'], inplace=True)
    df_lieux.drop(columns=['v2'], inplace=True)
    df_lieux.drop(columns=['id'], inplace=True, errors="ignore")
    # trop d'options différentes pour cette variable je ne sais pas la quel traiter.
    df_lieux.drop(columns=['nbv'], inplace=True)


    df_lieux.drop(columns=['lartpc'], inplace=True)



    data = get_all_usagers(db)

    if data:
        rows = [obj.__dict__ for obj in data]

        df_usagers = pd.DataFrame(rows)
    else:
        print("No data found.")

    df_usagers.dropna(subset=['an_nais'], inplace=True)
    df_usagers.reset_index(drop=True, inplace=True)
    for col in df_usagers.select_dtypes(include='object'):
        df_usagers[col] = df_usagers[col].str.strip()

    df_usagers.drop(columns=['id'], inplace=True, errors="ignore")

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




    data = get_all_vehicules(db)

    if data:
        rows = [obj.__dict__ for obj in data]
        df_vehicules = pd.DataFrame(rows)
    else:
        print("No data found.")


    for col in df_vehicules.select_dtypes(include='object'):
        df_vehicules[col] = df_vehicules[col].str.strip()
    df_vehicules.drop(columns=['occutc'], inplace=True)
    df_vehicules.drop(columns=['num_veh'], inplace=True)
    df_vehicules.drop(columns=['id'], inplace=True, errors="ignore")




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
        df.drop(columns=['_sa_instance_state'], inplace=True, errors='ignore')
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


    """
    à rajouté 
    4) bien vue pour age
    je pense nuit/jour pas possible de l'estimé là, on vas se basé sur lum, on dirait j'ai pas l'h de l'accident , 
    vma vraiment besoin de catégorisé ? je me rend pas bien compte.  explique le regroupement 

    1) rajouter les semaines / pas semaine + jours férié

    """


    """
    les jours semaine / pas semaine, à voir rajouté jours férie. 

    to make this we need to use the data : 
    jour = Column(Integer)
    mois = Column(Integer)
    an = Column(Integer, index=True)
    """


    def dates_to_features(df):
        """Convert jour, mois, an columns to day of week and is_holiday features."""
        
        import holidays
        
        # Initialize French holidays
        fr_holidays = holidays.France()
        
        # Create date column from jour, mois, an
        df['date'] = pd.to_datetime(df[['an', 'mois', 'jour']].rename(columns={'an': 'year', 'mois': 'month', 'jour': 'day'}), errors='coerce')
        
        # Extract day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df['date'].dt.dayofweek
        
        # Create is_weekend feature (1 if Saturday or Sunday, 0 otherwise)
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Determine if the date is a holiday
        df['is_holiday'] = df['date'].dt.date.apply(lambda x: 1 if x in fr_holidays else 0)
        
        
        return df


    """
    2) vma catégorisé  sauf gardé en brute pour model arbre
    a revoir ce que j'ai comme vma thought --> voir si les valeurs sont cohérentes dans le bins
    """
    def vma_to_categorical(df):
        """Convert vma column to categorical based on defined bins."""
        bins = [-1, 30, 50, 70, 90, 110, 130, float('inf')]
        labels = [0, 1, 2, 3, 4, 5, 6]  # Categorical labels
        
        df['vma_cat'] = pd.cut(df['vma'], bins=bins, labels=labels)
        
        return df


    def an_nais_to_age(df, current_year=None):
        """Convert an_nais column to age."""
        if current_year is None:
            if 'date' not in df.columns:
                df['date'] = pd.to_datetime(df[['an', 'mois', 'jour']].rename(columns={'an': 'year', 'mois': 'month', 'jour': 'day'}), errors='coerce')
            current_year = df['date'].dt.year
        
        df['age'] = current_year - df['an_nais']
        
        return df

    def add_time_encodings(df: pd.DataFrame, col: str = 'hrmn_scaled') -> pd.DataFrame:
        """
        Adds sine and cosine cyclical encodings for a scaled time column (0–1 range).

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame.
        col : str, optional
            Name of the scaled time column (default is 'hrmn_scaled').

        Returns
        -------
        pd.DataFrame
            The same DataFrame with two new columns: 'sin_time' and 'cos_time'.
        """
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")

        df = df.copy()
        df['sin_time'] = np.sin(2 * np.pi * df[col])
        df['cos_time'] = np.cos(2 * np.pi * df[col])
        df.drop(columns=[col], inplace=True)
        return df
    merged_df = dates_to_features(merged_df)
    merged_df = vma_to_categorical(merged_df)
    merged_df = an_nais_to_age(merged_df)
    merged_df = add_time_encodings(merged_df, col='hrmn_scaled')

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
                    #####
                    date=None if isna(row.get('date')) else row.get('date'),
                    day_of_week=None if isna(row.get('day_of_week')) else row.get('day_of_week'),
                    is_weekend=None if isna(row.get('is_weekend')) else row.get('is_weekend'),
                    is_holiday=None if isna(row.get('is_holiday')) else row.get('is_holiday'),
                    vma_cat=None if isna(row.get('vma_cat')) else row.get('vma_cat'),
                    age=None if isna(row.get('age')) else int(row.get('age')),
                    sin_time=None if isna(row.get('sin_time')) else float(row.get('sin_time')),
                    cos_time=None if isna(row.get('cos_time')) else float(row.get('cos_time')),
                    #####
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

    def check_if_csv_done():
        """check or folders :
            scripts/import_lieux.lock
            scripts/import_vehicules.lock
            scripts/import_usagers.lock
            scripts/import_caract.lock
        are absent
            """
        lock_files = [
            "scripts/import_lieux.lock",
            "scripts/import_vehicules.lock", 
            "scripts/import_usagers.lock",
            "scripts/import_caract.lock"
        ]
        
        # Return True if all lock files are absent (all imports done)
        return not any(check_lock_file(lock_file) for lock_file in lock_files)
                
    """
    this needs to run when all the data from the others dags are done.
    """
    if __name__ == "__main__":
        # Wait until all imports are complete
        while not check_if_csv_done():
            logging.info("Waiting for other imports to finish...")
            print("Waiting for other imports to finish...")
            time.sleep(10)    
            
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
except Exception as e:
    logging.error(f"AI Training Data import An error occurred: {e}\n{traceback.format_exc()}")




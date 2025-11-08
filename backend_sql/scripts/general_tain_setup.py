"""
setup le dag pour les script trainning models
"""
from scripts.extensions_scripts import check_lock_file, create_lock_file, remove_lock_file


def check_if_filtre_data_done():
    lock_files = [
        "scripts/import_ai_training_data.lock",
    ]
    
    # Return True if all lock files are absent (all imports done)
    return not any(check_lock_file(lock_file) for lock_file in lock_files)
                
"""
géré les columns qu'on veut jamais :
je prend pas les id id = Column(Integer, primary_key=True, index=True, autoincrement=True) 
id_accident = Column(BigInteger, index=True) id_usager = Column(BigInteger, index=True) 
id_vehicule = Column(BigInteger, index=True) 
date_ajout = Column(DateTime, default=datetime.now, nullable=False) 
"""

def get_columns_to_exclude():
    return [
        "id",
        "id_accident",
        "id_usager",
        "id_vehicule",
        "date_ajout",
    ]

def remove_excluded_columns(df):
    """Remove excluded columns from dataframe"""
    columns_to_exclude = get_columns_to_exclude()
    # Only drop columns that exist in the dataframe
    columns_to_drop = [col for col in columns_to_exclude if col in df.columns]
    return df.drop(columns=columns_to_drop)


"oui lat/long pas ouf a prendre en compte directement je pense on peut ignioré"
def remove_lat_long_columns(df):
    """Remove lat and long columns from dataframe"""
    columns_to_exclude = ["lat", "long"]
    # Only drop columns that exist in the dataframe
    columns_to_drop = [col for col in columns_to_exclude if col in df.columns]
    return df.drop(columns=columns_to_drop)



""" if not tree model we can remove VMA column """
def remove_vma_column(df):
    """Remove VMA column from dataframe"""
    if "vma" in df.columns:
        return df.drop(columns=["vma"])
    return df

""" if not needed we can remove an_nais column """
def remove_an_nais_column(df):
    """Remove an_nais column from dataframe"""
    if "an_nais" in df.columns:
        return df.drop(columns=["an_nais"])
    return df



def delete_hrmn_scaled_column(df):
    """Delete hrmn_scaled column from dataframe"""
    if "hrmn_scaled" in df.columns:
        return df.drop(columns=["hrmn_scaled"])
    return df

def delete_mois_jour_an_columns(df):
    """Delete mois, jour, an columns from dataframe"""
    columns_to_remove = []
    for col in ["mois", "jour", "an"]:
        if col in df.columns:
            columns_to_remove.append(col)
    if columns_to_remove:
        return df.drop(columns=columns_to_remove)
    return df


def delete_date_column(df):
    """Delete date column from dataframe"""
    if "date" in df.columns:
        return df.drop(columns=["date"])
    return df
"""


For tabular classification models (XGBoost, CatBoost, etc.):
➜ Keep jour, mois, and an as separate columns (maybe add weekday or is_weekend too). delete hrmn_scaled.

For sequence/time-series or deep models (e.g. Transformer, LSTM):
➜ Use a single datetime column, but transform it into meaningful numeric features (e.g. timestamp, sin/cos of month/day).
"""
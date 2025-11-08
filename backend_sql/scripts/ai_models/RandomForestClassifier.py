import sys
import os
import traceback
import logging
from xml.parsers.expat import model
import numpy as np

# Logging setup
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_folder, 'train_RandomForestClassifier_model.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
try:
    from sklearn.model_selection import train_test_split
    from sklearn.utils.class_weight import compute_class_weight
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    sys.path.append("/app")
    from routers.ai_training_model_data_router import get_all_ai_training_data
    import pandas as pd
    from database import SessionLocal
    from scripts.general_tain_setup import remove_excluded_columns, remove_lat_long_columns, remove_vma_column, remove_an_nais_column,delete_hrmn_scaled_column,delete_date_column
    db = SessionLocal()

   
    def data_set():
        data = get_all_ai_training_data(db)
        if data:
            rows = [obj.__dict__ for obj in data]
            df = pd.DataFrame(rows)
        else:
            logging.info("No data found.")
        logging.info(f"Dataframe columns before preprocessing: {df.columns}")
        df = remove_excluded_columns(df)
        df = remove_lat_long_columns(df)
        df = remove_vma_column(df)
        df = remove_an_nais_column(df)
        df = delete_hrmn_scaled_column(df)
        df = delete_date_column(df)
        df.drop(columns=['locp', 'is_weekend'], inplace=True)

        logging.info(f"Dataframe columns after preprocessing: {df.columns}")
        return df
        
    def prepare_data(df):
        """
        Prepare data for logistic regression
        """
       

        # Create a copy to avoid modifying original
        data = df.copy()
        
        # Remove unnecessary columns
        columns_to_drop = ['_sa_instance_state']
        data = data.drop(columns=[col for col in columns_to_drop if col in data.columns])
        
        # Separate target variable
        if 'grav' not in data.columns:
            raise ValueError("Target column 'grav' not found in dataframe")
        
        y = data['grav']
        X = data.drop('grav', axis=1)
        
        # Handle missing values
        # For numerical columns, fill with median
        numerical_cols = X.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            X[col].fillna(X[col].median(), inplace=True)
        
        # For categorical columns, fill with mode
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            X[col].fillna(X[col].mode()[0] if len(X[col].mode()) > 0 else 'Unknown', inplace=True)
        
        # Encode categorical variables
        label_encoders = {}
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
        
        return X, y, label_encoders
    

    def train_random_forest(X, y):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Compute class weights
        weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
        class_weights = dict(zip(np.unique(y), weights))

        logging.info("Training Random Forest Classifier...")
        """
        max_depth=10 (was None) - Most important! Stops trees from growing infinitely deep
        min_samples_split=20 (was 2) - Need at least 20 samples to split a node
        min_samples_leaf=10 (was 1) - Each leaf must have at least 10 samples
        max_samples=0.8 - Each tree sees only 80% of data, adds randomness
        n_estimators=100 (kept) - 300 was too many
        """
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            max_samples=0.8,
            random_state=42,
            class_weight=class_weights,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Evaluation
        logging.info("="*60)
        logging.info("TRAINING SET PERFORMANCE")
        logging.info("="*60)
        logging.info(f"Accuracy: {accuracy_score(y_train, y_pred_train):.4f}")

        logging.info("="*60)
        logging.info("TEST SET PERFORMANCE")
        logging.info("="*60)
        logging.info(f"Accuracy: {accuracy_score(y_test, y_pred_test):.4f}")

        logging.info("\nClassification Report:")
        logging.info(f"\n{classification_report(y_test, y_pred_test)}")

        logging.info("\nConfusion Matrix:")
        logging.info(f"\n{confusion_matrix(y_test, y_pred_test)}")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        logging.info("="*60)
        logging.info("TOP 10 MOST IMPORTANT FEATURES")
        logging.info("="*60)
        logging.info(f"\n{feature_importance.head(10).to_string(index=False)}")

        return model, X_train, X_test, y_train, y_test
    
    if __name__ == "__main__":  
        print("RandomForestClassifier script started")
        df = data_set()
        X, y, label_encoders = prepare_data(df)

        train_random_forest(X, y)
except Exception as e:
    logging.error(f"RandomForestClassifier import An error occurred: {e}\n{traceback.format_exc()}")




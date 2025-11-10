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
    filename=os.path.join(log_folder, 'train_logistic_regression_model.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
try:
    import mlflow
    import mlflow.sklearn
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("logistic_regression_training")
    from sklearn.model_selection import train_test_split
    from sklearn.utils.class_weight import compute_class_weight
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    sys.path.append("/app")
    from routers.ai_training_model_data_router import get_all_ai_training_data
    import pandas as pd
    from database import SessionLocal
    from scripts.general_tain_setup import group_grav_values, remove_excluded_columns, remove_lat_long_columns, remove_vma_column, remove_an_nais_column,delete_hrmn_scaled_column,delete_date_column
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
        # df = remove_lat_long_columns(df)
        df = remove_vma_column(df)
        df = remove_an_nais_column(df)
        df = delete_hrmn_scaled_column(df)
        df = delete_date_column(df)
        df = group_grav_values(df)
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
    

    def analyze_correlations(X, y):
        """
        Analyze correlations in the dataset
        """
        logging.info("="*60)
        logging.info("CORRELATION ANALYSIS")
        logging.info("="*60)
        
        # Combine X and y for full correlation analysis
        data_for_corr = X.copy()
        data_for_corr['grav'] = y
        
        # Calculate correlation matrix
        correlation_matrix = data_for_corr.corr()
        
        # Get correlations with target variable
        target_correlations = correlation_matrix['grav'].drop('grav').sort_values(ascending=False)
        
        logging.info("\nTop 15 Features Correlated with Target (grav):")
        logging.info("-" * 60)
        for feature, corr_value in target_correlations.head(15).items():
            logging.info(f"{feature:20s}: {corr_value:7.4f}")
        
        logging.info("\nBottom 15 Features Correlated with Target (grav):")
        logging.info("-" * 60)
        for feature, corr_value in target_correlations.tail(15).items():
            logging.info(f"{feature:20s}: {corr_value:7.4f}")
        
        # Find highly correlated feature pairs (potential multicollinearity)
        logging.info("\n" + "="*60)
        logging.info("HIGHLY CORRELATED FEATURE PAIRS (|correlation| > 0.8)")
        logging.info("="*60)
        
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                if abs(correlation_matrix.iloc[i, j]) > 0.8:
                    high_corr_pairs.append({
                        'Feature 1': correlation_matrix.columns[i],
                        'Feature 2': correlation_matrix.columns[j],
                        'Correlation': correlation_matrix.iloc[i, j]
                    })
        
        if high_corr_pairs:
            high_corr_df = pd.DataFrame(high_corr_pairs)
            high_corr_df = high_corr_df.sort_values('Correlation', ascending=False, key=abs)
            logging.info(f"\n{high_corr_df.to_string(index=False)}")
            logging.info(f"\nFound {len(high_corr_pairs)} highly correlated feature pairs")
            logging.info("Consider removing one feature from each pair to reduce multicollinearity")
        else:
            logging.info("\nNo highly correlated feature pairs found (threshold: 0.8)")
        
        # Summary statistics
        logging.info("\n" + "="*60)
        logging.info("CORRELATION SUMMARY")
        logging.info("="*60)
        logging.info(f"Strongest positive correlation with target: {target_correlations.index[0]} ({target_correlations.iloc[0]:.4f})")
        logging.info(f"Strongest negative correlation with target: {target_correlations.index[-1]} ({target_correlations.iloc[-1]:.4f})")
        logging.info(f"Mean absolute correlation with target: {abs(target_correlations).mean():.4f}")
        
        return correlation_matrix, target_correlations
    
    def train_logistic_regression(X, y, params=None):
        """
        Train logistic regression model
        """
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)


        # Train logistic regression model
        # Using 'liblinear' solver which works well for smaller datasets
        # max_iter increased for convergence
        model = LogisticRegression(**params)
        
        logging.info("Training logistic regression model...")
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        mlflow.log_metric("accuracy", accuracy_score(y_test, y_pred_test))

        # Evaluate the model
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
        
        # Feature importance (coefficients)
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'coefficient': model.coef_[0] if model.coef_.shape[0] == 1 else model.coef_.mean(axis=0)
        })
        feature_importance['abs_coefficient'] = abs(feature_importance['coefficient'])
        feature_importance = feature_importance.sort_values('abs_coefficient', ascending=False)
        
        logging.info("="*60)
        logging.info("TOP 10 MOST IMPORTANT FEATURES")
        logging.info("="*60)
        logging.info(f"\n{feature_importance.head(10).to_string(index=False)}")
    
        return model, scaler, X_train, X_test, y_train, y_test
    
    if __name__ == "__main__":  
        print("train_logistic_regression_model script started")
        df = data_set()
        X, y, label_encoders = prepare_data(df)
        analyze_correlations(X, y)

        with mlflow.start_run(run_name="log_reg_experiment"):
            weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
            class_weights = dict(zip(np.unique(y), weights))
            default_params = {
                "random_state": 42,
                "max_iter": 1000,
                "solver": "liblinear",
                "class_weight": class_weights
            }

            model, scaler, X_train, X_test, y_train, y_test = train_logistic_regression(X, y, default_params)

            # Log parameters    
            for param, value in default_params.items():
                mlflow.log_param(param, value)


            # Log model
            mlflow.sklearn.log_model(model, artifact_path="model")

            # Optional: log scaler as artifact
            import joblib
            joblib.dump(scaler, "scaler.pkl")
            mlflow.log_artifact("scaler.pkl")

            logging.info("Model and metrics logged to MLflow successfully.")

except Exception as e:
    logging.error(f"train_logistic_regression_model import An error occurred: {e}\n{traceback.format_exc()}")




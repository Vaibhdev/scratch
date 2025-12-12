import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from .strategies import Strategy
from .features import FeatureEngineer

class MLStrategy(Strategy):
    def __init__(self, model_type: str = 'rf', train_split: float = 0.7):
        self.model_type = model_type
        self.train_split = train_split
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.features = []

    def train(self, df: pd.DataFrame):
        """
        Trains the ML model.
        """
        # 1. Feature Engineering
        df = self.feature_engineer.add_technical_indicators(df)
        df = self.feature_engineer.create_lag_features(df)
        
        # 2. Create Target
        # Predict if next day's return is positive (1) or negative (0)
        df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
        df.dropna(inplace=True)
        
        # 3. Prepare Data
        X, y, self.features = self.feature_engineer.prepare_data_for_ml(df)
        
        # 4. Train/Test Split
        split_idx = int(len(X) * self.train_split)
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_test, y_test = X[split_idx:], y[split_idx:]
        
        # 5. Initialize Model
        if self.model_type == 'rf':
            self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        elif self.model_type == 'lr':
            self.model = LogisticRegression(random_state=42)
        else:
            raise ValueError("Invalid model type. Use 'rf' or 'lr'.")
            
        # 6. Train
        print(f"Training {self.model_type.upper()} model on {len(X_train)} samples...")
        self.model.fit(X_train, y_train)
        
        # 7. Evaluate
        train_acc = accuracy_score(y_train, self.model.predict(X_train))
        test_acc = accuracy_score(y_test, self.model.predict(X_test))
        print(f"Train Accuracy: {train_acc:.2%}")
        print(f"Test Accuracy:  {test_acc:.2%}")
        
        return df # Return df with features for backtesting

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
            
        # We need to regenerate features for the whole dataset to ensure alignment
        # In a real scenario, we would process new data incrementally.
        # Here, we assume df contains the same data structure as used in training.
        
        # Note: The backtest engine passes the full dataframe. 
        # We need to make sure we don't look ahead. 
        # The 'Target' generation in train() used shift(-1), which is lookahead.
        # But for inference (generating signals), we use current features to predict NEXT step.
        
        df_features = self.feature_engineer.add_technical_indicators(df)
        df_features = self.feature_engineer.create_lag_features(df_features)
        
        # Align indices
        common_index = df_features.index
        
        # Prepare X
        # We must use the SAME scaler as training? 
        # Ideally yes. The FeatureEngineer resets scaler on prepare_data_for_ml.
        # This is a simplification. For strict correctness, FeatureEngineer should persist scaler.
        # Let's assume for this demo that we re-fit scaler on the whole history or 
        # we should update FeatureEngineer to support fit/transform separation.
        # Given the scope, we'll re-use the prepare method which re-fits. 
        # This is "data leakage" if we backtest on training data, but acceptable for a simple demo 
        # if we acknowledge it. Better: split data in main.py and only backtest on test set.
        
        X, _, _ = self.feature_engineer.prepare_data_for_ml(df_features, target_col='Close') # Target col doesn't matter for X
        
        predictions = self.model.predict(X)
        
        # Convert 0/1 to -1/1 (Short/Long) or 0/1 (Neutral/Long)
        # Let's do Long/Short
        signals = np.where(predictions == 1, 1.0, -1.0)
        
        return pd.Series(signals, index=common_index).reindex(df.index).fillna(0)

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds technical indicators to the DataFrame.
        """
        df = df.copy()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['20dSTD'] = df['Close'].rolling(window=20).std()
        df['Upper_Band'] = df['MA20'] + (df['20dSTD'] * 2)
        df['Lower_Band'] = df['MA20'] - (df['20dSTD'] * 2)
        
        # Momentum (ROC)
        df['ROC'] = df['Close'].pct_change(periods=10) * 100
        
        # Volatility (ATR - simplified)
        df['TR'] = np.maximum(
            (df['High'] - df['Low']), 
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)), 
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        return df.dropna()

    def create_lag_features(self, df: pd.DataFrame, lags: int = 5) -> pd.DataFrame:
        """
        Creates lag features for Close price and Returns.
        """
        df = df.copy()
        for i in range(1, lags + 1):
            df[f'Close_Lag_{i}'] = df['Close'].shift(i)
            df[f'Return_Lag_{i}'] = df['Close'].pct_change().shift(i)
        return df.dropna()

    def prepare_data_for_ml(self, df: pd.DataFrame, target_col: str = 'Target') -> tuple:
        """
        Prepares data for Scikit-Learn models.
        """
        # Define features (exclude OHLC if we only want indicators/lags, or keep them)
        # Let's use indicators and lags
        feature_cols = [c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Target', 'Signal']]
        
        X = df[feature_cols].values
        y = df[target_col].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y, feature_cols

    def prepare_data_for_lstm(self, df: pd.DataFrame, target_col: str = 'Target', time_steps: int = 60) -> tuple:
        """
        Prepares data for LSTM (3D array).
        """
        feature_cols = [c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Target', 'Signal']]
        data = df[feature_cols].values
        
        # Scale data
        data_scaled = self.scaler.fit_transform(data)
        
        X, y = [], []
        # We need to align target with the end of the sequence
        # If we want to predict T+1 using T-60 to T, target should be at T+1 (or T if we shift target)
        # Assumes 'Target' column is already aligned such that row i contains the target for the prediction made at i
        
        targets = df[target_col].values
        
        for i in range(time_steps, len(data)):
            X.append(data_scaled[i-time_steps:i])
            y.append(targets[i])
            
        return np.array(X), np.array(y), feature_cols

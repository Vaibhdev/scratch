import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from .strategies import Strategy
from .features import FeatureEngineer

class LSTMStrategy(Strategy):
    def __init__(self, time_steps: int = 60, epochs: int = 10, batch_size: int = 32):
        self.time_steps = time_steps
        self.epochs = epochs
        self.batch_size = batch_size
        self.feature_engineer = FeatureEngineer()
        self.model = None

    def build_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(units=1, activation='sigmoid')) # Binary classification
        
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def train(self, df: pd.DataFrame):
        print("Preprocessing data for LSTM...")
        df = self.feature_engineer.add_technical_indicators(df)
        
        # Target: 1 if Close[t+1] > Close[t], else 0
        df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
        df.dropna(inplace=True)
        
        X, y, _ = self.feature_engineer.prepare_data_for_lstm(df, target_col='Target', time_steps=self.time_steps)
        
        # Split
        split = int(len(X) * 0.8)
        X_train, y_train = X[:split], y[:split]
        X_test, y_test = X[split:], y[split:]
        
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))
        
        print(f"Training LSTM on {len(X_train)} samples...")
        self.model.fit(X_train, y_train, epochs=self.epochs, batch_size=self.batch_size, validation_data=(X_test, y_test), verbose=1)
        
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if self.model is None:
            raise ValueError("Model not trained.")
            
        df_features = self.feature_engineer.add_technical_indicators(df)
        # Dummy target for shape alignment
        df_features['Target'] = 0 
        
        X, _, _ = self.feature_engineer.prepare_data_for_lstm(df_features, target_col='Target', time_steps=self.time_steps)
        
        # Predict
        probs = self.model.predict(X, verbose=0)
        predictions = (probs > 0.5).astype(int).flatten()
        
        # Align signals with original index
        # X starts at index `time_steps`
        # So prediction[0] corresponds to index `time_steps`
        
        signals = np.where(predictions == 1, 1.0, -1.0)
        
        # Create series aligned with df_features (which is slightly shorter than df due to indicators)
        # The LSTM consumes `time_steps` rows to make 1 prediction.
        # The prediction is for the NEXT step? 
        # In training: X[t-60:t] -> y[t] (Target at t).
        # So prediction at t is for the movement that happened at t (or will happen t+1?)
        # Our target definition: Target[t] = 1 if Close[t+1] > Close[t].
        # In prepare_data_for_lstm: y[i] = targets[i]. 
        # So X[i-60:i] predicts Target[i].
        # Target[i] is direction from i to i+1.
        # So at time i, we use history up to i to predict direction i->i+1.
        # This is correct for trading at i (Close) to hold until i+1.
        
        # The signals series needs to match the original index.
        # We pad the beginning with 0s.
        
        valid_index = df_features.index[self.time_steps:]
        signal_series = pd.Series(signals, index=valid_index)
        
        return signal_series.reindex(df.index).fillna(0)

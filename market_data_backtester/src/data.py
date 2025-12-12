import pandas as pd
import yfinance as yf
from typing import Optional

class DataLoader:
    def __init__(self):
        pass

    def load_data(self, ticker: str, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
        """
        Loads OHLC data from yfinance.
        """
        print(f"Downloading data for {ticker} from {start_date} to {end_date}...")
        df = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=False)
        
        if df.empty:
            raise ValueError(f"No data found for {ticker}")

        # Ensure we have a DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Handle multi-level columns if any (yfinance sometimes returns them)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Keep only required columns and ensure they are numeric
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df[required_cols].copy()
        
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df.dropna(inplace=True)
        
        return df

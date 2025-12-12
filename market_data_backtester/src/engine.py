import pandas as pd
import numpy as np
from .data import DataLoader
from .strategies import Strategy
from .performance import calculate_sharpe_ratio, calculate_max_drawdown, calculate_total_return, calculate_volatility

class BacktestEngine:
    def __init__(self, data_loader: DataLoader, strategy: Strategy, initial_capital: float = 10000.0):
        self.data_loader = data_loader
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.results = {}

    def run(self, ticker: str, start_date: str, end_date: str):
        # 1. Load Data
        df = self.data_loader.load_data(ticker, start_date, end_date)
        
        # 2. Generate Signals
        signals = self.strategy.generate_signals(df)
        
        # 3. Calculate Returns
        # Market Returns (Log returns are often better for additivity, but simple returns are standard for basic backtests)
        df['Market_Returns'] = df['Close'].pct_change()
        
        # Strategy Returns
        # Shift signals by 1 because we trade at the Close based on data available up to that Close, 
        # so the return we get is the NEXT day's return. 
        # Or if we assume we trade at the Open of the next day?
        # Standard vectorized assumption: Signal calculated at Close t, Position held from Close t to Close t+1.
        # So we multiply Signal(t) * Return(t+1).
        df['Signal'] = signals
        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Market_Returns']
        
        # Handle NaN from shifting
        df.dropna(inplace=True)
        
        # 4. Calculate Equity Curve
        df['Cumulative_Market_Returns'] = (1 + df['Market_Returns']).cumprod()
        df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        
        df['Equity'] = self.initial_capital * df['Cumulative_Strategy_Returns']
        
        # 5. Calculate Metrics
        sharpe = calculate_sharpe_ratio(df['Strategy_Returns'])
        max_dd = calculate_max_drawdown(df['Cumulative_Strategy_Returns'])
        total_ret = calculate_total_return(df['Cumulative_Strategy_Returns'])
        volatility = calculate_volatility(df['Strategy_Returns'])
        
        self.results = {
            'ticker': ticker,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'total_return_pct': total_ret,
            'volatility': volatility,
            'final_equity': df['Equity'].iloc[-1],
            'data': df
        }
        
        return self.results

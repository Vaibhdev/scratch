import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Takes a DataFrame with OHLC data and returns a Series of signals.
        1: Buy, -1: Sell, 0: Hold/Neutral
        """
        pass

class MovingAverageCrossover(Strategy):
    def __init__(self, short_window: int = 50, long_window: int = 200):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        close = df['Close']
        
        short_mavg = close.rolling(window=self.short_window, min_periods=1).mean()
        long_mavg = close.rolling(window=self.long_window, min_periods=1).mean()
        
        # Create signals
        # 1 where short > long, 0 otherwise
        # We want to capture the crossover, but for a simple backtest, 
        # being "in the market" when short > long is the standard trend following approach.
        # So we'll return 1 when short > long, and 0 (or -1) otherwise.
        # Let's stick to Long-Only for simplicity unless specified otherwise, 
        # but the prompt implies "strategies", so let's support Long/Short or Long/Cash.
        # Let's do Long (1) when Short > Long, else Neutral (0).
        
        signals = np.where(short_mavg > long_mavg, 1.0, 0.0)
        
        return pd.Series(signals, index=df.index)

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, buy_threshold: int = 30, sell_threshold: int = 70):
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals = pd.Series(0, index=df.index)
        
        # Mean Reversion Logic:
        # Buy when RSI < 30 (Oversold)
        # Sell when RSI > 70 (Overbought)
        # This is slightly stateful because you hold until the exit signal.
        # Vectorizing stateful logic is harder. 
        # For a purely vectorized approach without loops, we can use regime definitions.
        # But standard RSI is: Buy on cross up 30, Sell on cross down 70.
        # Let's implement a simple version: 1 if RSI < 30, -1 if RSI > 70, else 0.
        # This is "contrarian" - betting on reversal.
        
        signals[rsi < self.buy_threshold] = 1.0
        signals[rsi > self.sell_threshold] = -1.0
        
        # Note: This simple signal generation doesn't hold positions between signals.
        # A proper backtester engine handles "holding" state. 
        # If the engine is stateless, this strategy will only trade on the specific days of extreme RSI.
        # We will assume the Engine handles position management (e.g. fill forward) or 
        # we make the strategy return "Target Position" instead of "Trade Signal".
        # Let's make the strategy return "Target Position" (1 for long, -1 for short, 0 for flat).
        # For RSI, this is tricky without a loop. 
        # Let's stick to the prompt's "vectorized operations".
        # We can forward fill signals to simulate holding?
        # Let's try: Buy (1) triggers holding until Sell (-1).
        
        signals = signals.replace(0, np.nan).ffill().fillna(0)
        
        return signals

class MomentumStrategy(Strategy):
    def __init__(self, period: int = 10):
        self.period = period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Simple Momentum: Price > Price N days ago
        momentum = df['Close'] - df['Close'].shift(self.period)
        signals = np.where(momentum > 0, 1.0, 0.0)
        return pd.Series(signals, index=df.index)

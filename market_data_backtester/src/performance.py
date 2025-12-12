import numpy as np
import pandas as pd

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    """
    Calculates the annualized Sharpe Ratio.
    """
    if returns.std() == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    return np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())

def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
    """
    Calculates the Maximum Drawdown.
    """
    # cumulative_returns should be an equity curve (e.g. starting at 1.0)
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def calculate_total_return(cumulative_returns: pd.Series) -> float:
    """
    Calculates total return percentage.
    """
    if cumulative_returns.empty:
        return 0.0
    return (cumulative_returns.iloc[-1] - 1.0) * 100

def calculate_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculates annualized volatility.
    """
    return returns.std() * np.sqrt(periods_per_year)

def calculate_cagr(cumulative_returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculates Compound Annual Growth Rate (CAGR).
    """
    if cumulative_returns.empty:
        return 0.0
    
    total_return = cumulative_returns.iloc[-1]
    n_years = len(cumulative_returns) / periods_per_year
    
    if n_years == 0:
        return 0.0
        
    return (total_return ** (1 / n_years)) - 1

def calculate_win_rate(returns: pd.Series) -> float:
    """
    Calculates the percentage of positive return periods.
    """
    if returns.empty:
        return 0.0
    
    wins = (returns > 0).sum()
    total = len(returns)
    return wins / total

def calculate_confusion_matrix(y_true, y_pred):
    """
    Calculates confusion matrix metrics.
    """
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred)
    return cm


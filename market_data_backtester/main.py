import argparse
import matplotlib.pyplot as plt
from src.data import DataLoader
from src.strategies import MovingAverageCrossover, RSIStrategy, MomentumStrategy
from src.ml_strategies import MLStrategy
from src.dl_strategies import LSTMStrategy
from src.engine import BacktestEngine
from src.performance import calculate_cagr, calculate_win_rate

def main():
    parser = argparse.ArgumentParser(description='Market Data Backtester')
    parser.add_argument('--ticker', type=str, default='AAPL', help='Stock ticker symbol')
    parser.add_argument('--start', type=str, default='2020-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2023-01-01', help='End date (YYYY-MM-DD)')
    parser.add_argument('--strategy', type=str, choices=['sma', 'rsi', 'momentum', 'rf', 'lr', 'lstm'], default='sma', help='Strategy to use')
    parser.add_argument('--initial_capital', type=float, default=10000.0, help='Initial capital')
    parser.add_argument('--train_start', type=str, default='2010-01-01', help='Training start date for ML/DL')
    parser.add_argument('--train_end', type=str, default='2019-12-31', help='Training end date for ML/DL')
    
    args = parser.parse_args()
    
    # 1. Initialize Data Loader
    loader = DataLoader()
    
    # 2. Initialize Strategy
    if args.strategy == 'sma':
        strategy = MovingAverageCrossover(short_window=50, long_window=200)
    elif args.strategy == 'rsi':
        strategy = RSIStrategy(period=14, buy_threshold=30, sell_threshold=70)
    elif args.strategy == 'momentum':
        strategy = MomentumStrategy(period=10)
    elif args.strategy in ['rf', 'lr']:
        strategy = MLStrategy(model_type=args.strategy)
    elif args.strategy == 'lstm':
        strategy = LSTMStrategy(epochs=5) # Reduced epochs for demo
        
    # 2.5 Train Model (if ML/DL)
    if args.strategy in ['rf', 'lr', 'lstm']:
        print(f"\nTraining {args.strategy.upper()} model from {args.train_start} to {args.train_end}...")
        train_df = loader.load_data(args.ticker, args.train_start, args.train_end)
        strategy.train(train_df)
        print("Training complete.\n")
        
    # 3. Initialize Engine
    engine = BacktestEngine(loader, strategy, args.initial_capital)
    
    # 4. Run Backtest
    try:
        results = engine.run(args.ticker, args.start, args.end)
        
        # 5. Print Results
        print("\n" + "="*40)
        print(f"Backtest Results for {args.ticker} ({args.strategy.upper()})")
        print("="*40)
        print(f"Initial Capital:   ${args.initial_capital:,.2f}")
        print(f"Final Equity:      ${results['final_equity']:,.2f}")
        print(f"Total Return:      {results['total_return_pct']:.2f}%")
        print(f"CAGR:              {calculate_cagr(results['data']['Cumulative_Strategy_Returns']):.2%}")
        print(f"Win Rate:          {calculate_win_rate(results['data']['Strategy_Returns']):.2%}")
        print(f"Sharpe Ratio:      {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:      {results['max_drawdown']:.2%}")
        print(f"Volatility:        {results['volatility']:.2%}")
        print("="*40 + "\n")
        
        # 6. Plotting (Optional)
        df = results['data']
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['Cumulative_Market_Returns'], label='Market (Buy & Hold)', alpha=0.6)
        plt.plot(df.index, df['Cumulative_Strategy_Returns'], label='Strategy', alpha=0.8)
        plt.title(f'Equity Curve: {args.ticker} - {args.strategy.upper()}')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Returns')
        plt.legend()
        plt.grid(True)
        
        # Save plot instead of showing it (headless environment)
        plt.savefig('backtest_result.png')
        print("Plot saved to backtest_result.png")
        
    except Exception as e:
        print(f"Error running backtest: {e}")

if __name__ == "__main__":
    main()


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_and_clean_data(filepath):
    """
    Loads historical market data, standardizes column names, 
    and prepares the time-series index.
    """
    # Load the raw dataset (Note: pd.read_csv takes the filepath argument, not a hardcoded string)
    df = pd.read_csv("xauusd_5m_clean.csv")
    
    # Standardize column names to lowercase for easier referencing
    df.columns = [col.lower() for col in df.columns]
    
    # Catch the 'date', 'time', or 'datetime' column and set as DatetimeIndex
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    elif 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
    # Drop any rows with missing values to prevent miscalculations later
    df.dropna(inplace=True)
    
    # Ensure we have the required OHLCV columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Dataset is missing one of the required columns: {required_cols}")
        
    print(f"Data successfully loaded. Total rows: {len(df)}")
    return df

# --- Execution ---
# You will replace 'xauusd_15m.csv' with your actual file path
data = load_and_clean_data('xauusd_5m_clean.csv')
print(data.head())



def add_ema_indicators(df, fast_period=9, slow_period=21):
    """
    Adds Fast and Slow Exponential Moving Averages (EMA) for trend detection.
    Default periods (9 and 21) are optimized for short-term intraday momentum.
    """
    # Calculate the Exponential Moving Averages
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    return df



def add_supply_demand_zones(df, window=20):
    """
    Identifies dynamic support (demand) and resistance (supply) levels 
    using a rolling window of recent local minimums and maximums.
    """
    # The 'window' parameter determines how many previous candles to look back at.
    # A 20-period window on a 15m chart represents 5 hours of price action.
    
    df['demand_zone'] = df['low'].rolling(window=window, min_periods=1).min()
    df['supply_zone'] = df['high'].rolling(window=window, min_periods=1).max()
    
    return df


# --- Execution ---
data = load_and_clean_data('xauusd_5m_clean.csv')
data = add_ema_indicators(data, fast_period=9, slow_period=21)
data = add_supply_demand_zones(data, window=20)
print(data[['close', 'ema_fast', 'ema_slow']].tail())


def generate_signals(df):
    """
    Generates Buy (1) and Sell (-1) signals based on EMA crossovers
    occurring near Supply and Demand zones.
    """
    # Initialize the signal column with 0 (No trade)
    df['signal'] = 0
    
    # Create boolean columns for the crossover logic
    # Fast > Slow = Bullish phase | Fast < Slow = Bearish phase
    bullish_phase = df['ema_fast'] > df['ema_slow']
    bearish_phase = df['ema_fast'] < df['ema_slow']
    
    # Detect the exact candle the crossover happens (shift(1) looks at previous candle)
    bullish_crossover = bullish_phase & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1))
    bearish_crossover = bearish_phase & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1))
    
    # Define proximity to zones (e.g., price is within 0.1% of the zone)
    # This ensures we are taking trades at the "bend" off structural levels
    threshold = 0.001 
    near_demand = df['low'] <= df['demand_zone'] * (1 + threshold)
    near_supply = df['high'] >= df['supply_zone'] * (1 - threshold)
    
    # Trigger Signals: Crossover + Near Zone
    df.loc[bullish_crossover & near_demand, 'signal'] = 1
    df.loc[bearish_crossover & near_supply, 'signal'] = -1
    
    return df

# --- Execution ---
data = generate_signals(data)
print(f"Total Buy Signals: {len(data[data['signal'] == 1])}")
print(f"Total Sell Signals: {len(data[data['signal'] == -1])}")


def simulate_trades(df):
    """
    Simulates executing trades based on signals.
    Enforces a dynamic stop-loss outside supply/demand zones 
    and a strict 1:2 Risk/Reward Take Profit.
    """
    trades = []
    in_trade = False
    trade_type = None
    entry_price = 0
    sl = 0
    tp = 0
    entry_time = None

    # Buffer to place SL slightly outside the exact zone (0.05% buffer)
    buffer = 0.0005 

    for index, row in df.iterrows():
        # 1. Manage Active Trades
        if in_trade:
            if trade_type == 'Buy':
                # Check if SL hit (price dropped below SL)
                if row['low'] <= sl:
                    trades.append({'entry_time': entry_time, 'exit_time': index, 'type': 'Buy', 
                                   'entry': entry_price, 'exit': sl, 'pnl': sl - entry_price, 'result': 'Loss'})
                    in_trade = False
                # Check if TP hit (price rose above TP)
                elif row['high'] >= tp:
                    trades.append({'entry_time': entry_time, 'exit_time': index, 'type': 'Buy', 
                                   'entry': entry_price, 'exit': tp, 'pnl': tp - entry_price, 'result': 'Win'})
                    in_trade = False

            elif trade_type == 'Sell':
                # Check if SL hit (price rose above SL)
                if row['high'] >= sl:
                    trades.append({'entry_time': entry_time, 'exit_time': index, 'type': 'Sell', 
                                   'entry': entry_price, 'exit': sl, 'pnl': entry_price - sl, 'result': 'Loss'})
                    in_trade = False
                # Check if TP hit (price dropped below TP)
                elif row['low'] <= tp:
                    trades.append({'entry_time': entry_time, 'exit_time': index, 'type': 'Sell', 
                                   'entry': entry_price, 'exit': tp, 'pnl': entry_price - tp, 'result': 'Win'})
                    in_trade = False
        
        # 2. Enter New Trades
        if not in_trade and row['signal'] != 0:
            entry_time = index
            entry_price = row['close']
            
            if row['signal'] == 1: # Buy Signal
                trade_type = 'Buy'
                # Place SL slightly below the demand zone
                sl = row['demand_zone'] * (1 - buffer)
                risk = entry_price - sl
                
                # Filter out anomalies where risk is 0 or negative
                if risk > 0: 
                    tp = entry_price + (risk * 2) # 1:2 Risk/Reward
                    in_trade = True
                
            elif row['signal'] == -1: # Sell Signal
                trade_type = 'Sell'
                # Place SL slightly above the supply zone
                sl = row['supply_zone'] * (1 + buffer)
                risk = sl - entry_price
                
                # Filter out anomalies
                if risk > 0: 
                    tp = entry_price - (risk * 2) # 1:2 Risk/Reward
                    in_trade = True

    # Convert the list of trade dictionaries into a Pandas DataFrame
    trades_df = pd.DataFrame(trades)
    return trades_df

# --- Execution ---
trades_df = simulate_trades(data)
print(f"Total Trades Executed: {len(trades_df)}")
print(trades_df.head(10))




def calculate_kpis_and_plot(trades_df):
    """
    Calculates key performance indicators (KPIs) from the trade ledger 
    and generates a visual equity curve.
    """
    # Prevent errors if no trades were executed
    if trades_df.empty:
        print("No trades to evaluate.")
        return

    # 1. Calculate Metrics
    total_trades = len(trades_df)
    wins = len(trades_df[trades_df['result'] == 'Win'])
    losses = len(trades_df[trades_df['result'] == 'Loss'])
    
    win_rate = (wins / total_trades) * 100
    
    gross_profit = trades_df[trades_df['result'] == 'Win']['pnl'].sum()
    gross_loss = trades_df[trades_df['result'] == 'Loss']['pnl'].sum() # This will be a negative number
    net_profit = gross_profit + gross_loss 
    
    # Profit Factor is Gross Profit / Gross Loss (Absolute value)
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')

    # 2. Print the Formal Performance Report
    print("\n" + "="*50)
    print("      ALGORITHMIC STRATEGY PERFORMANCE REPORT      ")
    print("="*50)
    print(f"Total Trades Executed: {total_trades}")
    print(f"Win Rate:              {win_rate:.2f}% ({wins}W / {losses}L)")
    print(f"Gross Profit:          {gross_profit:.2f} points")
    print(f"Gross Loss:            {gross_loss:.2f} points")
    print(f"Net PnL:               {net_profit:.2f} points")
    print(f"Profit Factor:         {profit_factor:.2f}")
    print("="*50 + "\n")

    # 3. Generate the Equity Curve
    # Calculate cumulative PnL for the Y-axis
    trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
    
    # Ensure exit_time is treated as a datetime object for the X-axis
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])

    plt.figure(figsize=(12, 6))
    plt.plot(trades_df['exit_time'], trades_df['cumulative_pnl'], color='#1f77b4', linewidth=2, label='Strategy Equity')
    
    # Formatting the chart for a professional look
    plt.title('Algorithmic Strategy Backtest: Cumulative PnL', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Profit / Loss (Points)', fontsize=12)
    
    # Add a baseline at zero
    plt.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    
    # Grid and legend
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper left')
    
    # Adjust layout to prevent clipping of dates
    plt.tight_layout()
    
    # Display the plot
    plt.show()

# --- Execution ---
# Note: Ensure you have matplotlib installed (pip install matplotlib)
calculate_kpis_and_plot(trades_df)
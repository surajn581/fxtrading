import pandas as pd
import numpy as np

def calculate_impulse_macd(data, short_period=12, long_period=26, signal_period=9):
    # Calculate MACD
    data['EMA_short'] = data['mid'].ewm(span=short_period, min_periods=short_period).mean()
    data['EMA_long'] = data['mid'].ewm(span=long_period, min_periods=long_period).mean()
    data['MACD'] = data['EMA_short'] - data['EMA_long']
    
    # Calculate Signal Line
    data['Signal_line'] = data['MACD'].ewm(span=signal_period, min_periods=signal_period).mean()
    
    # Calculate Impulse Line (difference between MACD and Signal Line)
    data['Impulse_Line'] = data['MACD'] - data['Signal_line']
    
    # Calculate Impulse Histogram (difference between Impulse Line and its previous value)
    data['Impulse_Histogram'] = data['Impulse_Line'].diff()
    
    return data

def calculate_technical_indicators(data):
    # Calculate Moving Averages (SMA)
    data['SMA_20'] = data['mid'].rolling(window=20).mean()
    data['SMA_50'] = data['mid'].rolling(window=50).mean()
    
    # Calculate Relative Strength Index (RSI)
    delta = data['mid'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate Bollinger Bands
    data['middle_band'] = data['mid'].rolling(window=20).mean()
    data['std_dev'] = data['mid'].rolling(window=20).std()
    data['upper_band'] = data['middle_band'] + 2 * data['std_dev']
    data['lower_band'] = data['middle_band'] - 2 * data['std_dev']

    data = calculate_impulse_macd(data)
    
    return data

def generate_signals(data):
    signals = pd.DataFrame(index=data.index)
    signals['action'] = 'Hold'
    signals['amount'] = 0
    
    # Calculate technical indicators
    data = calculate_technical_indicators(data)
    
    # Generate signals based on indicators
    signals['signal'] = 0  # 0 means hold
    
    # Buy signals
    signals.loc[(data['SMA_20'] > data['SMA_50']) & (data['RSI'] < 30) & (data['mid'] < data['lower_band']), 'signal'] = 1
    
    # Sell signals
    signals.loc[(data['SMA_20'] < data['SMA_50']) & (data['RSI'] > 70) & (data['mid'] > data['upper_band']), 'signal'] = -1
    
    # Determine actions and amounts
    signals.loc[signals['signal'] == 1, 'action'] = 'Buy'
    signals.loc[signals['signal'] == -1, 'action'] = 'Sell'
    
    # Assuming a fixed amount to trade (you can adjust this based on your strategy)
    signals.loc[signals['signal'] != 0, 'amount'] = 100  # Example: Trading 100 units each time
    
    return signals[['action', 'amount']]

# Example usage:
# Assume 'data' is your pandas DataFrame with columns 'mid', 'quoteSize', and 'timeStamp'

def loadData():
# Generate example data (simulate 180 days of 5-minute data)
    np.random.seed(0)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=180*24*12, freq='5T')
    data = pd.DataFrame({
        'mid': np.random.uniform(1.1, 1.2, len(dates)),  # Simulating mid prices
        'quoteSize': np.random.randint(1000, 5000, len(dates)),
        'timeStamp': dates
    })
    return data

def doTrading():
    data = loadData()
    # Apply trading strategy
    signals = generate_signals(data)

    print(signals.tail())  # Print the last few rows of signals DataFrame

    return signals
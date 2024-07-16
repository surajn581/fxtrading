import pandas as pd
import numpy as np

def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    # Calculate MACD
    data['EMA_short'] = data['mid'].ewm(span=short_period, min_periods=short_period).mean()
    data['EMA_long'] = data['mid'].ewm(span=long_period, min_periods=long_period).mean()
    data['MACD'] = data['EMA_short'] - data['EMA_long']    
    # Calculate Signal Line
    data['Signal_line'] = data['MACD'].ewm(span=signal_period, min_periods=signal_period).mean()
    return data

def calculate_technical_indicators(data):
    # Calculate Moving Averages (SMA)
    data['SMA_short'] = data['mid'].rolling(window=10).mean()
    data['SMA_long'] = data['mid'].rolling(window=50).mean()
    
    # Calculate Relative Strength Index (RSI)
    delta = data['mid'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data = calculate_macd(data)
    return data

def sma_signal(data):
    data['signal'] = -1
    data['sma_signal'] = None
    data.loc[(data['SMA_short'] > data['SMA_long']), 'signal'] = 1
    data.loc[(data['SMA_short'] < data['SMA_long']), 'signal'] = 0
    data['signal'] = data['signal'].diff()
    data.loc[(data['signal'] == -1), 'sma_signal'] = 1
    data.loc[(data['signal'] == 1), 'sma_signal'] = -1
    data.drop(columns=['signal'], inplace=True)
    data['sma_signal'] = data['sma_signal'].fillna(0)
    return data

def rsi_signal(data):
    data['signal'] = -1
    data['rsi_signal'] = None
    data.loc[(data['RSI'] >= 70), 'signal'] = 0
    data.loc[(data['RSI'] <= 30), 'signal'] = 1
    data['signal'] = data['signal'].diff()
    data.loc[(data['signal'] == 2), 'rsi_signal'] = 1
    data.loc[(data['signal'] == 1), 'rsi_signal'] = -1
    data.drop(columns=['signal'], inplace=True)
    data['rsi_signal'] = data['rsi_signal'].fillna(0)
    return data

def macd_signal(data):    
    data['signal'] = 0
    data['macd_signal'] = None
    data.loc[(data['MACD'] > data['Signal_line']), 'signal'] = 1
    data.loc[(data['MACD'] < data['Signal_line']), 'signal'] = 0
    data['signal'] = data['signal'].diff()
    data.loc[(data['signal'] == -1), 'macd_signal'] = -1
    data.loc[(data['signal'] == 1), 'macd_signal'] = 1
    data.drop(columns=['signal'], inplace=True)
    data['macd_signal'] = data['macd_signal'].fillna(0)
    return data

def generate_signals(data):
    data = calculate_technical_indicators(data)
    data = sma_signal(data)
    data = rsi_signal(data)
    data = macd_signal(data)
    final_signal = data['sma_signal'] + data['rsi_signal'] + data['macd_signal']
    data['signal'] = final_signal
    return data

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
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def check_stock(symbol, date, interval='5m'):
    # Calculate window size for 2 hours based on interval
    if interval.endswith('m'):
        minutes = int(interval[:-1])
        window_size = 120 // minutes
    else:
        return False  # Handle other intervals if needed
    
    # Fetch data
    start_date = date.strftime('%Y-%m-%d')
    end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval, prepost=False)
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return False
    print(data)

    if data.empty:
        return False
    
    # Localize index to NY timezone
    data.index = data.index.tz_convert('America/New_York')
    
    # Filter regular market hours (9:30 AM to 4:00 PM)
    data = data.between_time('09:30', '16:00')
    
    if data.empty:
        return False
    
    # Get open price
    O = data.iloc[0]['Open']
    
    # Calculate high percentage
    data['high_pct'] = (data['High'] - O) / O * 100
    
    # Find peaks (>10%)
    peaks = data[data['high_pct'] > 10]
    if peaks.empty:
        return False
    
    first_peak = peaks.index[0]
    
    # Post-peak data
    post_peak = data.loc[first_peak:]
    
    if len(post_peak) < window_size:
        return False
    
    # Check price containment
    post_peak['in_range'] = (post_peak['Low'] >= O * 1.06) & (post_peak['High'] <= O * 1.08)
    
    # Check for consecutive window
    post_peak['rolling_sum'] = post_peak['in_range'].rolling(window=window_size, min_periods=window_size).sum()
    
    return (post_peak['rolling_sum'] >= window_size).any()

# Example usage
if __name__ == "__main__":
    symbols = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'META']
    target_date = datetime.now().date() - timedelta(days=1)  # Yesterday's data
    
    print(f"Checking stocks for {target_date}")
    qualifying = []
    
    for symbol in symbols:
        if check_stock(symbol, target_date):
            qualifying.append(symbol)
    
    if qualifying:
        print("Stocks meeting criteria:", ', '.join(qualifying))
    else:
        print("No stocks met the criteria")
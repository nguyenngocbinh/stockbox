"""
Vnstock Helper Functions
Helper functions để thay thế VNDirectClient bằng vnstock
"""

import pandas as pd
import datetime
from vnstock import Vnstock

def get_stock_data_vnstock(tickers, start_date=None, end_date=None, interval='1D'):
    """
    Lấy dữ liệu cổ phiếu cho nhiều ticker bằng vnstock
    
    Args:
        tickers (list): Danh sách mã cổ phiếu
        start_date (str): Ngày bắt đầu (YYYY-MM-DD)
        end_date (str): Ngày kết thúc (YYYY-MM-DD)
        interval (str): Khoảng thời gian ('1D', '1W', '1M')
    
    Returns:
        pd.DataFrame: DataFrame với multi-index [Symbol, Date]
    """
    if start_date is None:
        start_date = "2020-01-01"
    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    all_data = []
    
    for ticker in tickers:
        try:
            print(f"Đang lấy dữ liệu cho {ticker}...")
            stock = Vnstock().stock(symbol=ticker, source='VCI')
            data = stock.quote.history(start=start_date, end=end_date, interval=interval)
            
            # Thêm cột Symbol
            data['Symbol'] = ticker
            
            # Đổi tên cột để tương thích
            if 'time' not in data.columns and 'date' in data.columns:
                data['Date'] = pd.to_datetime(data['date'])
            elif data.index.name in ['date', 'time'] or 'datetime' in str(type(data.index[0])):
                data['Date'] = pd.to_datetime(data.index)
            else:
                data['Date'] = pd.to_datetime(data.index)
            
            # Đảm bảo có đủ các cột cần thiết
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    # Thử tìm cột tương tự
                    possible_names = {
                        'open': ['Open', 'OPEN'],
                        'high': ['High', 'HIGH'],
                        'low': ['Low', 'LOW'], 
                        'close': ['Close', 'CLOSE'],
                        'volume': ['Volume', 'VOLUME', 'vol']
                    }
                    for possible_name in possible_names.get(col, []):
                        if possible_name in data.columns:
                            data[col] = data[possible_name]
                            break
            
            # Tạo cột Adj Close nếu chưa có
            if 'adjClose' in data.columns:
                data['Adj Close'] = data['adjClose']
            elif 'adj_close' in data.columns:
                data['Adj Close'] = data['adj_close']
            else:
                data['Adj Close'] = data['close']
            
            # Rename columns để khớp với format cũ
            column_mapping = {
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            data.rename(columns=column_mapping, inplace=True)
            
            all_data.append(data)
            
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu cho {ticker}: {e}")
            continue
    
    if all_data:
        # Kết hợp tất cả dữ liệu
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Set multi-index như VNDirectClient
        combined_data.set_index(['Symbol', 'Date'], inplace=True)
        
        return combined_data
    else:
        raise ValueError("Không thể lấy dữ liệu cho bất kỳ ticker nào")

def calculate_returns_vnstock(data):
    """
    Tính toán returns cho dữ liệu từ vnstock
    
    Args:
        data (pd.DataFrame): DataFrame với multi-index [Symbol, Date]
        
    Returns:
        pd.DataFrame: DataFrame với các cột returns added
    """
    returns_data = data.copy()
    returns_data.sort_index(inplace=True)
    
    # Calculate returns for different periods
    returns_data['1d%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change()
    returns_data['1w%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change(periods=5)
    returns_data['1m%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change(periods=20)
    returns_data['6m%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change(periods=120)
    
    return returns_data

def vnstock_ohlcv_wrapper(tickers, start_date=None, end_date=None):
    """
    Wrapper function để thay thế VNDirectClient().ohlcv()
    
    Args:
        tickers (list): Danh sách mã cổ phiếu
        start_date (str): Ngày bắt đầu
        end_date (str): Ngày kết thúc
        
    Returns:
        pd.DataFrame: OHLCV data với format tương tự VNDirectClient
    """
    return get_stock_data_vnstock(tickers, start_date, end_date)

def vnstock_returns_wrapper(ohlcv_data):
    """
    Wrapper function để thay thế VNDirectClient().calculate_returns()
    
    Args:
        ohlcv_data (pd.DataFrame): OHLCV data
        
    Returns:
        pd.DataFrame: Data với returns calculated
    """
    return calculate_returns_vnstock(ohlcv_data)

"""
Vnstock Helper Functions
Helper functions để thay thế VNDirectClient bằng vnstock

Features:
- Silent import và execution (không print thông báo)
- Error handling graceful
- Rate limiting và retry logic cho VCI API
- Tương thích với cấu trúc dữ liệu VNDirectClient
- Verbose mode có thể bật nếu cần debug
"""

import pandas as pd
import datetime
import time
import random
import warnings
import sys
import contextlib
from io import StringIO

# Silent import của Vnstock
try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        import contextlib
        from io import StringIO
        
        # Suppress all output during import
        with contextlib.redirect_stdout(StringIO()), contextlib.redirect_stderr(StringIO()):
            from vnstock import Vnstock
except ImportError:
    print("Warning: vnstock not available")
    Vnstock = None

# Silent context manager
@contextlib.contextmanager
def silent_mode():
    """Context manager to suppress all output"""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        with contextlib.redirect_stdout(StringIO()), contextlib.redirect_stderr(StringIO()):
            yield

def create_stock_silent(symbol, source='TCBS'):
    """Create stock object in silent mode"""
    with silent_mode():
        return Vnstock().stock(symbol=symbol, source=source)

# Rate limiting utilities
def safe_api_call(func, stock_obj, *args, max_retries=3, **kwargs):
    """
    Safely call API with automatic source switching (TCBS -> VCI) on error
    """
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check if it's any API error and we haven't tried switching yet
            if attempt < max_retries - 1:
                # Try switching to VCI source
                try:
                    print(f"TCBS error detected. Switching to VCI source... (attempt {attempt + 1}/{max_retries})")
                    print(f"Error was: {e}")
                    
                    # Create new stock object with VCI source
                    symbol = getattr(stock_obj, 'symbol', None) or getattr(stock_obj, '_symbol', None)
                    if symbol:
                        # Create new stock with VCI in silent mode
                        new_stock = create_stock_silent(symbol, source='VCI')
                        
                        # Try with VCI using same parameters
                        with silent_mode():
                            result = new_stock.quote.history(*args, **kwargs)
                        print(f"✅ Successfully switched to VCI for {symbol}")
                        return result
                    else:
                        print("❌ Could not determine symbol for VCI fallback")
                        
                except Exception as vci_error:
                    print(f"❌ VCI fallback failed: {vci_error}")
                    # Continue to next retry
                
                # If both sources fail, wait before retry
                delay = 2 + random.uniform(0, 1) * (2 ** attempt)
                print(f"Both TCBS and VCI failed. Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                continue
            
            # For final attempt, re-raise
            else:
                print(f"Max retries reached. Final error: {e}")
                raise e
    
    return None

def get_stock_data_vnstock(tickers, start_date=None, end_date=None, interval='1D', verbose=False):
    """
    Lấy dữ liệu cổ phiếu cho nhiều ticker bằng vnstock
    
    Args:
        tickers (list): Danh sách mã cổ phiếu
        start_date (str): Ngày bắt đầu (YYYY-MM-DD)
        end_date (str): Ngày kết thúc (YYYY-MM-DD)
        interval (str): Khoảng thời gian ('1D', '1W', '1M')
        verbose (bool): In thông báo progress hay không
    
    Returns:
        pd.DataFrame: DataFrame với multi-index [Symbol, Date]
    """
    if Vnstock is None:
        raise ImportError("vnstock package is not available. Please install: pip install vnstock")
    
    if start_date is None:
        start_date = "2021-01-01"
    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    all_data = []
    
    for i, ticker in enumerate(tickers):
        try:
            if verbose:
                print(f"Đang lấy dữ liệu cho {ticker}... ({i+1}/{len(tickers)})")
            
            # Start with TCBS as default source (more stable) in silent mode
            stock = create_stock_silent(ticker, source='TCBS')
            
            # Use safe_api_call wrapper with automatic TCBS->VCI switching
            if verbose:
                data = safe_api_call(
                    stock.quote.history,
                    stock,  # Pass stock object for source switching
                    start=start_date,
                    end=end_date,
                    interval=interval
                )
            else:
                # Silent mode for API call too
                with silent_mode():
                    data = safe_api_call(
                        stock.quote.history,
                        stock,  # Pass stock object for source switching
                        start=start_date,
                        end=end_date,
                        interval=interval
                    )
            
            if data is None:
                if verbose:
                    print(f"Không thể lấy dữ liệu cho {ticker} sau nhiều lần thử")
                continue
            
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
            if verbose:
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

def vnstock_ohlcv_wrapper(tickers, start_date=None, end_date=None, verbose=False):
    """
    Wrapper function để thay thế VNDirectClient().ohlcv()
    
    Args:
        tickers (list): Danh sách mã cổ phiếu
        start_date (str): Ngày bắt đầu
        end_date (str): Ngày kết thúc
        verbose (bool): In thông báo progress hay không
        
    Returns:
        pd.DataFrame: OHLCV data với format tương tự VNDirectClient
    """
    return get_stock_data_vnstock(tickers, start_date, end_date, verbose=verbose)

def vnstock_returns_wrapper(ohlcv_data):
    """
    Wrapper function để thay thế VNDirectClient().calculate_returns()
    
    Args:
        ohlcv_data (pd.DataFrame): OHLCV data
        
    Returns:
        pd.DataFrame: Data với returns calculated
    """
    return calculate_returns_vnstock(ohlcv_data)

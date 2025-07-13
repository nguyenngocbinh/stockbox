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
def safe_api_call(func, stock_obj, *args, verbose=False, max_retries=3, **kwargs):
    """
    Safely call API with automatic source switching (TCBS -> VCI) on error
    """
    for attempt in range(max_retries):
        try:
            if verbose:
                result = func(*args, **kwargs)
            else:
                # Use silent mode for API call
                with silent_mode():
                    result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check for rate limit or any TCBS error on first attempt
            is_rate_limit = ("rate" in error_str or "limit" in error_str or 
                           "quá nhiều request" in error_str or 
                           error_type == "RateLimitExceeded" or
                           "tcbs" in error_str)
            
            if attempt == 0 and is_rate_limit:
                # First attempt failed due to rate limit, try VCI immediately
                try:
                    if verbose:
                        print(f"TCBS rate limit detected. Switching to VCI source...")
                        print(f"TCBS Error: {e}")
                    
                    # Create new stock object with VCI source
                    symbol = getattr(stock_obj, 'symbol', None) or getattr(stock_obj, '_symbol', None)
                    if symbol:
                        # Create new stock with VCI in silent mode
                        new_stock = create_stock_silent(symbol, source='VCI')
                        
                        # Try with VCI using same parameters
                        if verbose:
                            result = new_stock.quote.history(*args, **kwargs)
                            print(f"✅ Successfully switched to VCI for {symbol}")
                        else:
                            with silent_mode():
                                result = new_stock.quote.history(*args, **kwargs)
                        return result
                    else:
                        if verbose:
                            print("❌ Could not determine symbol for VCI fallback")
                        
                except Exception as vci_error:
                    if verbose:
                        print(f"❌ VCI fallback failed: {vci_error}")
                    # Continue to retry logic below
            
            # For non-rate-limit errors or after VCI fails, use traditional retry
            if attempt < max_retries - 1:
                delay = 2 + random.uniform(0, 1) * (2 ** attempt)
                if verbose:
                    print(f"API error on attempt {attempt + 1}. Retrying in {delay:.1f} seconds...")
                    print(f"Error: {e}")
                time.sleep(delay)
                continue
            else:
                if verbose:
                    print(f"Max retries reached. Final error: {e}")
                raise e
    
    return None

def get_stock_data_vnstock(tickers, start_date=None, end_date=None, interval='1D', verbose=False):
    """
    Lấy dữ liệu cổ phiếu cho nhiều ticker bằng vnstock với chunking theo thời gian
    
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
    
    # Check if date range is large (> 1 year) to enable chunking
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    days_diff = (end_dt - start_dt).days
    
    # If more than 365 days, chunk by year to avoid rate limits
    use_chunking = days_diff > 365
    
    if use_chunking and verbose:
        print(f"📅 Large date range detected ({days_diff} days). Using yearly chunks to avoid rate limits.")
    
    all_data = []
    
    for i, ticker in enumerate(tickers):
        try:
            if verbose:
                print(f"Đang lấy dữ liệu cho {ticker}... ({i+1}/{len(tickers)})")
            
            ticker_data = []
            
            if use_chunking:
                # Chia theo từng năm
                current_start = start_dt
                while current_start < end_dt:
                    current_end = min(
                        current_start.replace(year=current_start.year + 1),
                        end_dt
                    )
                    
                    chunk_start = current_start.strftime("%Y-%m-%d")
                    chunk_end = current_end.strftime("%Y-%m-%d")
                    
                    if verbose:
                        print(f"  📊 Fetching {ticker} for {chunk_start} to {chunk_end}")
                    
                    # Get data for this chunk
                    chunk_data = _get_single_period_data(
                        ticker, chunk_start, chunk_end, interval, verbose
                    )
                    
                    if chunk_data is not None and not chunk_data.empty:
                        ticker_data.append(chunk_data)
                    
                    # Add delay between chunks to avoid rate limit
                    if current_end < end_dt:
                        delay = 2 + random.uniform(0, 1)
                        if verbose:
                            print(f"  ⏳ Waiting {delay:.1f}s between chunks...")
                        time.sleep(delay)
                    
                    current_start = current_end
            else:
                # Single request for small date ranges
                chunk_data = _get_single_period_data(
                    ticker, start_date, end_date, interval, verbose
                )
                if chunk_data is not None and not chunk_data.empty:
                    ticker_data.append(chunk_data)
            
            # Combine all chunks for this ticker
            if ticker_data:
                combined_ticker_data = pd.concat(ticker_data, ignore_index=True)
                # Remove duplicates and sort
                combined_ticker_data = combined_ticker_data.drop_duplicates(subset=['Symbol', 'Date'])
                combined_ticker_data = combined_ticker_data.sort_values('Date')
                all_data.append(combined_ticker_data)
            elif verbose:
                print(f"  ❌ No data retrieved for {ticker}")
            
            # Add delay between tickers
            if i < len(tickers) - 1:
                delay = 1 + random.uniform(0, 0.5)
                if verbose:
                    print(f"⏳ Waiting {delay:.1f}s before next ticker...")
                time.sleep(delay)
            
        except Exception as e:
            if verbose:
                print(f"❌ Lỗi khi lấy dữ liệu cho {ticker}: {e}")
            continue
    
    if all_data:
        # Kết hợp tất cả dữ liệu
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Set multi-index như VNDirectClient
        combined_data.set_index(['Symbol', 'Date'], inplace=True)
        
        if verbose:
            print(f"✅ Successfully retrieved {combined_data.shape[0]} records for {len(all_data)} tickers")
        
        return combined_data
    else:
        raise ValueError("Không thể lấy dữ liệu cho bất kỳ ticker nào")

def _get_single_period_data(ticker, start_date, end_date, interval, verbose):
    """
    Helper function để lấy dữ liệu cho một ticker trong một khoảng thời gian
    """
    try:
        # Start with TCBS as default source (more stable) in silent mode
        stock = create_stock_silent(ticker, source='TCBS')
        
        # Use safe_api_call wrapper with automatic TCBS->VCI switching
        data = safe_api_call(
            stock.quote.history,
            stock,  # Pass stock object for source switching
            start=start_date,
            end=end_date,
            interval=interval,
            verbose=verbose  # Pass verbose flag to safe_api_call
        )
        
        if data is None or data.empty:
            return None
        
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
        
        return data
        
    except Exception as e:
        if verbose:
            print(f"  ❌ Error getting data for {ticker} ({start_date} to {end_date}): {e}")
        return None

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

"""
VNDIRECT - API

This module provides a class to fetch and process stock data from the VNDIRECT API.
It handles data retrieval, processing, and calculation of various metrics.
"""

import os
import json
import time
from datetime import datetime, timedelta
import concurrent.futures
from typing import List, Dict, Union, Optional, Tuple, Any

import pandas as pd
import numpy as np
import requests
from requests.exceptions import RequestException


class VNDirectClient:
    """
    A client for fetching and analyzing Vietnamese stock market data from VNDIRECT API.
    
    This client provides comprehensive functionality for Vietnamese stock market analysis including
    data retrieval with caching, OHLCV processing, technical indicators calculation, and data export.
    
    Features:
    - Fetch historical stock data from VNDIRECT API with retry logic
    - Intelligent caching system with configurable expiry
    - Parallel data fetching for multiple tickers
    - Process raw data into standardized OHLCV format
    - Calculate returns over various time periods (1d, 1w, 1m, 6m)
    - Calculate volatility metrics with rolling windows
    - Resample data to different time frequencies
    - Export data in multiple formats (CSV)
    - Comprehensive error handling and validation
    
    Attributes:
        base_url (str): Base URL for the VNDIRECT API endpoint
        tickers (List[str]): List of 3-character stock ticker symbols
        size (int): Number of historical records to fetch per ticker (default: 125)
        verbose (bool): Enable verbose logging output
        cache_dir (str): Directory path for caching downloaded data
        use_cache (bool): Whether to use local caching (default: True)
        cache_expiry (int): Cache expiry time in hours (default: 24)
        request_timeout (int): HTTP request timeout in seconds (default: 10)
        max_retries (int): Maximum retry attempts for failed requests (default: 3)
        retry_delay (int): Delay between retry attempts in seconds (default: 1)
        raw_data (pd.DataFrame): Raw stock data as received from API
        ohlcv_df (pd.DataFrame): Processed OHLCV data with multi-index
        returns_data (pd.DataFrame): Data with calculated returns and metrics
    
    Example:
        >>> client = VNDirectClient(['VIC', 'VHM', 'FPT'], size=100, verbose=True)
        >>> data = client.get_data()
        >>> ohlcv = client.ohlcv()
        >>> returns = client.calculate_returns()
        >>> client.export_to_csv('stock_data.csv', 'ohlcv')
    """
    
    # Default headers for API requests
    HEADERS = {
        'content-type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # API configuration
    API_CONFIG = {
        'vndirect': {
            'base_url': "https://finfo-api.vndirect.com.vn/v4/stock_prices/",
            'sort_param': "date",
            'size_param': "size",
            'page_param': "page",
            'query_param': "q",
        }
    }

    def __init__(self, 
                 tickers: List[str], 
                 size: int = 125, 
                 verbose: bool = False,
                 use_cache: bool = True,
                 cache_dir: str = ".vnstock_cache",
                 cache_expiry: int = 24,
                 request_timeout: int = 10,
                 max_retries: int = 3,
                 retry_delay: int = 1):
        """
        Initialize the VNDirectClient class.
        
        Args:
            tickers: List of stock tickers to fetch data for
            size: Number of historical records to fetch per ticker
            verbose: Whether to print verbose output
            use_cache: Whether to use cached data when available
            cache_dir: Directory to cache data
            cache_expiry: Cache expiry time in hours
            request_timeout: Timeout for API requests in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = self.API_CONFIG['vndirect']['base_url']
        self.tickers = tickers
        self.size = size
        self.verbose = verbose
        
        # Cache settings
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        self.cache_expiry = cache_expiry
        
        # Request settings
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Data containers
        self.raw_data = None
        self.ohlcv_df = None
        self.returns_data = None
        
        # Create cache directory if it doesn't exist
        if self.use_cache and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # Validate inputs
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """
        Validate input parameters.
        
        Raises:
            ValueError: If any input parameters are invalid
        """
        if not self.tickers:
            raise ValueError("tickers list cannot be empty")
        
        if not all(isinstance(ticker, str) for ticker in self.tickers):
            raise ValueError("All tickers must be strings")
        
        if not all(len(ticker) == 3 for ticker in self.tickers):
            raise ValueError("All tickers must be 3 characters in length")
        
        if self.size <= 0:
            raise ValueError("size must be positive")
        
        if self.cache_expiry < 0:
            raise ValueError("cache_expiry must be non-negative")
    
    def _get_cache_path(self, ticker: str) -> str:
        """
        Get the cache file path for a ticker.
        
        Args:
            ticker: The stock ticker
            
        Returns:
            str: Path to the cache file
        """
        return os.path.join(self.cache_dir, f"{ticker}_size_{self.size}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """
        Check if a cache file is valid (exists and not expired).
        
        Args:
            cache_path: Path to the cache file
            
        Returns:
            bool: True if the cache is valid, False otherwise
        """
        if not os.path.exists(cache_path):
            return False
        
        if self.cache_expiry == 0:  # 0 means never expire
            return True
        
        file_time = os.path.getmtime(cache_path)
        file_datetime = datetime.fromtimestamp(file_time)
        expiry_time = datetime.now() - timedelta(hours=self.cache_expiry)
        
        return file_datetime > expiry_time
    
    def _save_to_cache(self, ticker: str, data: List[Dict]) -> None:
        """
        Save data to cache.
        
        Args:
            ticker: The stock ticker
            data: Data to cache
        """
        if not self.use_cache:
            return
        
        cache_path = self._get_cache_path(ticker)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to save cache for {ticker}: {str(e)}")
    
    def _load_from_cache(self, ticker: str) -> Optional[List[Dict]]:
        """
        Load data from cache.
        
        Args:
            ticker: The stock ticker
            
        Returns:
            Optional[List[Dict]]: Cached data if available and valid, None otherwise
        """
        if not self.use_cache:
            return None
        
        cache_path = self._get_cache_path(ticker)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to load cache for {ticker}: {str(e)}")
            return None
    
    def _fetch_ticker_data(self, ticker: str) -> Tuple[str, Optional[List[Dict]], Optional[str]]:
        """
        Fetch data for a single ticker with retries.
        
        Args:
            ticker: The stock ticker
            
        Returns:
            Tuple[str, Optional[List[Dict]], Optional[str]]: 
                Tuple of (ticker, data, error_message)
        """
        # Try to load from cache first
        cached_data = self._load_from_cache(ticker)
        if cached_data is not None:
            if self.verbose:
                print(f"Using cached data for {ticker}")
            return ticker, cached_data, None
        
        # Define the endpoint
        endpoint = f"code:{ticker}"
        
        # Set query parameters
        params = {
            self.API_CONFIG['vndirect']['sort_param']: self.API_CONFIG['vndirect']['sort_param'],
            self.API_CONFIG['vndirect']['size_param']: self.size,
            self.API_CONFIG['vndirect']['page_param']: 1,
            self.API_CONFIG['vndirect']['query_param']: endpoint,
        }
        
        # Try to fetch data with retries
        for attempt in range(self.max_retries):
            try:
                if self.verbose and attempt > 0:
                    print(f"Retry {attempt} for {ticker}")
                
                # Send the HTTP request
                res = requests.get(
                    self.base_url, 
                    params=params, 
                    headers=self.HEADERS,
                    timeout=self.request_timeout
                )
                
                # Check if the HTTP request was successful
                if res.status_code != 200:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return ticker, None, f"HTTP error {res.status_code}"
                
                # Extract data
                response_data = res.json()
                data = response_data.get("data", [])
                
                # Check if data is empty
                if not data:
                    return ticker, None, "No data available"
                
                # Cache the data
                self._save_to_cache(ticker, data)
                
                return ticker, data, None
            
            except RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return ticker, None, f"Request error: {str(e)}"
            
            except Exception as e:
                return ticker, None, f"Unexpected error: {str(e)}"
    
    def get_data(self, use_parallel: bool = True, max_workers: int = 5) -> pd.DataFrame:
        """
        Retrieve historical stock data for all tickers.
        
        Args:
            use_parallel: Whether to use parallel processing
            max_workers: Maximum number of worker threads for parallel processing
            
        Returns:
            pd.DataFrame: DataFrame containing historical stock data
            
        Raises:
            ValueError: If no data could be retrieved for any ticker
        """
        if self.verbose:
            print(f"Retrieving data for {len(self.tickers)} tickers")
        
        all_data = []
        failed_tickers = []
        
        if use_parallel and len(self.tickers) > 1:
            # Use parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(self._fetch_ticker_data, self.tickers))
                
                for ticker, data, error in results:
                    if data:
                        df_ticker = pd.DataFrame(data)
                        df_ticker["date"] = pd.to_datetime(df_ticker["date"])
                        all_data.append(df_ticker)
                    else:
                        failed_tickers.append((ticker, error))
        else:
            # Use sequential processing
            for ticker in self.tickers:
                if self.verbose:
                    print(f"Retrieving data for ticker: {ticker}")
                
                _, data, error = self._fetch_ticker_data(ticker)
                
                if data:
                    df_ticker = pd.DataFrame(data)
                    df_ticker["date"] = pd.to_datetime(df_ticker["date"])
                    all_data.append(df_ticker)
                else:
                    failed_tickers.append((ticker, error))
        
        # Report failures
        if failed_tickers:
            if self.verbose or len(failed_tickers) == len(self.tickers):
                print(f"Failed to retrieve data for {len(failed_tickers)} tickers:")
                for ticker, error in failed_tickers:
                    print(f"  - {ticker}: {error}")
        
        # Combine all data
        if not all_data:
            raise ValueError("Could not retrieve data for any ticker")
        
        self.raw_data = pd.concat(all_data, ignore_index=True)
        return self.raw_data
    
    def ohlcv(self) -> pd.DataFrame:
        """
        Process raw data into OHLCV format.
        
        Returns:
            pd.DataFrame: DataFrame containing OHLCV data
            
        Raises:
            ValueError: If no data is available
        """
        if self.raw_data is None or self.raw_data.empty:
            raise ValueError("No data available. Call get_data() first.")
        
        # Define required columns
        required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'adClose', 'nmVolume']
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in self.raw_data.columns]
        if missing_columns:
            raise ValueError(f"Data is missing required columns: {missing_columns}")
        
        # Create OHLCV DataFrame
        ohlcv_df = self.raw_data[required_columns].copy()
        
        # Rename columns to standard names
        ohlcv_df.columns = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
        # Set index
        ohlcv_df.set_index(['Symbol', 'Date'], inplace=True)
        
        self.ohlcv_df = ohlcv_df
        return self.ohlcv_df
    
    def resample(self, rule: str, col_list: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Resample the OHLCV data to a different frequency.
        
        Args:
            rule: The resampling rule (e.g., 'M' for monthly, 'W' for weekly)
            col_list: List of columns to resample. Default is all columns.
            
        Returns:
            pd.DataFrame: Resampled data
            
        Raises:
            ValueError: If OHLCV data is not available
        """
        if self.ohlcv_df is None or self.ohlcv_df.empty:
            raise ValueError("OHLCV data not available. Call ohlcv() first.")
        
        if col_list is None:
            col_list = self.ohlcv_df.columns
        else:
            # Validate column names
            invalid_cols = [col for col in col_list if col not in self.ohlcv_df.columns]
            if invalid_cols:
                raise ValueError(f"Invalid column names: {invalid_cols}")
        
        # Group by 'Symbol' and apply resampling to the specified columns
        resampled_data = self.ohlcv_df.groupby('Symbol')[col_list].resample(rule).last()
        
        return resampled_data
    
    def calculate_returns(self) -> pd.DataFrame:
        """
        Calculate returns for various time periods.
        
        Returns:
            pd.DataFrame: DataFrame with calculated returns
            
        Raises:
            ValueError: If OHLCV data is not available
        """
        if self.ohlcv_df is None or self.ohlcv_df.empty:
            raise ValueError("OHLCV data not available. Call ohlcv() first.")
        
        returns_data = self.ohlcv_df.copy()
        returns_data.sort_index(inplace=True)
        
        # Calculate returns for different periods
        returns_data['1d%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change()
        returns_data['1w%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change(periods=5)
        returns_data['1m%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change(periods=20)
        returns_data['6m%'] = returns_data.groupby('Symbol')['Adj Close'].pct_change(periods=120)
        
        self.returns_data = returns_data
        return self.returns_data
    
    def calculate_volatility(self, window: int = 20) -> pd.DataFrame:
        """
        Calculate volatility (standard deviation of returns) for each ticker.
        
        Args:
            window: Window size for rolling standard deviation
            
        Returns:
            pd.DataFrame: DataFrame with volatility data
            
        Raises:
            ValueError: If returns data is not available
        """
        if self.returns_data is None or self.returns_data.empty:
            raise ValueError("Returns data not available. Call calculate_returns() first.")
        
        # Calculate daily returns if not already calculated
        if '1d%' not in self.returns_data.columns:
            self.returns_data['1d%'] = self.returns_data.groupby('Symbol')['Adj Close'].pct_change()
        
        # Calculate rolling volatility
        volatility_data = self.returns_data.copy()
        volatility_data['volatility'] = volatility_data.groupby('Symbol')['1d%'].rolling(window=window).std().reset_index(level=0, drop=True)
        
        return volatility_data
    
    def get_latest_prices(self) -> pd.DataFrame:
        """
        Get the latest prices for all tickers.
        
        Returns:
            pd.DataFrame: DataFrame with latest prices
            
        Raises:
            ValueError: If OHLCV data is not available
        """
        if self.ohlcv_df is None or self.ohlcv_df.empty:
            raise ValueError("OHLCV data not available. Call ohlcv() first.")
        
        # Get the latest price for each ticker
        latest_prices = self.ohlcv_df.groupby('Symbol').last()
        
        return latest_prices
    
    def export_to_csv(self, filename: str, data_type: str = 'ohlcv') -> None:
        """
        Export data to a CSV file.
        
        Args:
            filename: Name of the CSV file
            data_type: Type of data to export ('raw', 'ohlcv', 'returns')
            
        Raises:
            ValueError: If the specified data is not available
        """
        if data_type == 'raw':
            if self.raw_data is None or self.raw_data.empty:
                raise ValueError("Raw data not available. Call get_data() first.")
            data = self.raw_data
        elif data_type == 'ohlcv':
            if self.ohlcv_df is None or self.ohlcv_df.empty:
                raise ValueError("OHLCV data not available. Call ohlcv() first.")
            data = self.ohlcv_df.reset_index()
        elif data_type == 'returns':
            if self.returns_data is None or self.returns_data.empty:
                raise ValueError("Returns data not available. Call calculate_returns() first.")
            data = self.returns_data.reset_index()
        else:
            raise ValueError(f"Invalid data_type: {data_type}. Must be 'raw', 'ohlcv', or 'returns'.")
        
        data.to_csv(filename, index=False)
        
        if self.verbose:
            print(f"Data exported to {filename}")
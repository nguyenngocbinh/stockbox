import pandas as pd
from typing import List, Union, Optional

def format_up_down_percent(val):
    """Format percentage values with red/green colors"""
    if pd.isna(val):
        return ''
    try:
        color = '#dc3545' if val < 0 else '#28a745'  # Bootstrap colors
        return f'color: {color}; font-weight: 600'
    except Exception:
        return ''

def format_milion(val):
    """Format values in millions"""
    if pd.isna(val):
        return ''
    return f"${val:,.1f}M"

def format_thousand(val):
    """Format values in thousands"""  
    if pd.isna(val):
        return ''
    return f"${val:,.0f}"

def format_df(returns_data, sort_by='6m%'):
    """
    Format DataFrame for display with enhanced styling
    Compatible with pandas >= 1.3.0
    
    Args:
        returns_data: DataFrame to format
        sort_by: Column name or list of column names to sort by
        
    Returns:
        Styled DataFrame ready for display
    """
    returns_data = returns_data.copy()
    
    # Format Volume and Price columns
    if 'Volume' in returns_data.columns:
        returns_data['Volume'] = pd.to_numeric(returns_data['Volume'], errors='coerce')
        returns_data['Volume'] = (returns_data['Volume'] / 1e6).apply(format_milion)
    
    if 'Adj Close' in returns_data.columns:
        returns_data['Price'] = pd.to_numeric(returns_data['Adj Close'], errors='coerce').apply(format_thousand)
    
    # Get latest data per symbol
    returns_data = returns_data.groupby('Symbol').tail(1)
    
    # Select required columns
    required_columns = ['Industry', 'Symbol', 'Price', '1d%', "1w%", "1m%", "6m%", 'Volume']
    available_columns = [col for col in required_columns if col in returns_data.columns]
    returns_data = returns_data[available_columns]
    
    # Sort data
    if isinstance(sort_by, str) and sort_by in returns_data.columns:
        returns_data = returns_data.sort_values(sort_by, ascending=False)
    elif isinstance(sort_by, list):
        available_sort_cols = [col for col in sort_by if col in returns_data.columns]
        if available_sort_cols:
            returns_data = returns_data.sort_values(available_sort_cols, ascending=[False] * len(available_sort_cols))
    
    # Set index
    index_columns = ['Industry', 'Symbol']
    available_index_cols = [col for col in index_columns if col in returns_data.columns]
    if available_index_cols:
        returns_data = returns_data.set_index(available_index_cols)

    # Apply basic styling
    styled_df = returns_data.style
    
    # Format percentage columns with background gradient
    percentage_cols = ['1d%', "1w%", "1m%", "6m%"]
    available_pct_cols = [col for col in percentage_cols if col in returns_data.columns]
    
    if available_pct_cols:
        # Format percentages
        styled_df = styled_df.format(subset=available_pct_cols, formatter="{:.2%}")
        
        # Add color mapping for percentage columns
        for col in available_pct_cols:
            styled_df = styled_df.map(
                lambda val: f"color: {'#dc3545' if val < 0 else '#28a745'}; font-weight: 600",
                subset=[col]
            )
            
            # Add background gradient
            styled_df = styled_df.background_gradient(
                cmap='RdYlGn',
                subset=[col],
                vmin=-0.2,
                vmax=0.2,
                axis=None
            )
    
    # Set table styles for better appearance
    styled_df = styled_df.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#f8f9fa'), 
                                       ('color', '#495057'),
                                       ('font-weight', 'bold'),
                                       ('border', '1px solid #dee2e6'),
                                       ('padding', '8px')]},
        {'selector': 'td', 'props': [('border', '1px solid #dee2e6'),
                                       ('padding', '8px'),
                                       ('text-align', 'right')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#f8f9fa')]},
        {'selector': '', 'props': [('border-collapse', 'collapse'),
                                   ('width', '100%'),
                                   ('font-size', '14px')]},
    ])
    
    # Set sticky headers and index
    try:
        styled_df = styled_df.set_sticky(axis="index")
        styled_df = styled_df.set_sticky(axis="columns")
    except Exception:
        pass
    
    # Add caption
    styled_df = styled_df.set_caption("📊 Stock Price Summary - Latest Data")
    
    return styled_df

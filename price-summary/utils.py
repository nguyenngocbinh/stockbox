import pandas as pd

def format_up_down_percent(val):
    """Format percentage values with red/green colors"""
    if pd.isna(val):
        return ''
    try:
        color = 'red' if val < 0 else 'green'
        return f'color: {color}'
    except:
        return ''

def format_milion(val):
    """Format values in millions"""
    return f"${val:.1f}M"

def format_thousand(val):
    """Format values in thousands"""  
    return f"${val:.1f}K"

def format_df(returns_data, sort_by='6m%'):
    """
    Format DataFrame for display with styling
    Simplified version for maximum compatibility
    """
    returns_data = returns_data.copy()
    
    # Format Volume and Price columns
    if 'Volume' in returns_data.columns:
        returns_data['Volume'] = (returns_data['Volume'] / 1e6).apply(format_milion)
    
    if 'Adj Close' in returns_data.columns:
        returns_data['Price'] = (returns_data['Adj Close']).apply(format_thousand)
    
    # Get latest data per symbol
    returns_data = returns_data.groupby('Symbol').tail(1)
    
    # Select required columns
    required_columns = ['Industry', 'Symbol', 'Price', '1d%', "1w%", "1m%", "6m%", 'Volume']
    available_columns = [col for col in required_columns if col in returns_data.columns]
    returns_data = returns_data[available_columns]
    
    # Sort data
    if isinstance(sort_by, str) and sort_by in returns_data.columns:
        returns_data.sort_values(sort_by, inplace=True)
    elif isinstance(sort_by, list):
        available_sort_cols = [col for col in sort_by if col in returns_data.columns]
        if available_sort_cols:
            returns_data.sort_values(available_sort_cols, inplace=True)
    
    # Set index
    index_columns = ['Industry', 'Symbol']
    available_index_cols = [col for col in index_columns if col in returns_data.columns]
    if available_index_cols:
        returns_data.set_index(available_index_cols, inplace=True)

    # Apply basic styling only
    styled_df = returns_data.style
    
    # Format percentage columns
    percentage_cols = ['1d%', "1w%", "1m%", "6m%"]
    available_pct_cols = [col for col in percentage_cols if col in returns_data.columns]
    
    if available_pct_cols:
        try:
            styled_df = styled_df.format(subset=pd.IndexSlice[:, available_pct_cols], formatter="{:.2%}")
        except:
            # Fallback to simple format
            format_dict = {col: "{:.2%}" for col in available_pct_cols}
            styled_df = styled_df.format(format_dict)
    
    # Try to add color styling (optional - won't break if fails)
    try:
        def highlight_negative(val):
            """Highlight negative values in red, positive in green"""
            if pd.isna(val):
                return ''
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        
        # Apply color styling with multiple fallback methods
        styling_applied = False
        
        # Method 1: Try map (pandas 1.3+)
        if not styling_applied:
            try:
                for col in available_pct_cols:
                    styled_df = styled_df.map(highlight_negative, subset=pd.IndexSlice[:, [col]])
                styling_applied = True
            except:
                pass
        
        # Method 2: Try applymap (older pandas)
        if not styling_applied:
            try:
                for col in available_pct_cols:
                    styled_df = styled_df.applymap(highlight_negative, subset=pd.IndexSlice[:, [col]])
                styling_applied = True
            except:
                pass
        
        # Method 3: Apply without subset (simplest)
        if not styling_applied:
            try:
                styled_df = styled_df.applymap(lambda x: highlight_negative(x) if isinstance(x, (int, float)) else '')
                styling_applied = True
            except:
                pass
                
    except Exception as e:
        # Color styling failed, but that's OK - we still have the formatted data
        pass
    
    # Try to set sticky index (optional)
    try:
        styled_df = styled_df.set_sticky(axis="index")
    except:
        pass  # Not supported in all pandas versions
    
    return styled_df

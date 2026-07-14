# 📈 Stockbox - Vietnamese Stock Analysis Platform

Nền tảng phân tích kỹ thuật chứng khoán Việt Nam với các chỉ báo RSI, MACD và theo dõi giá.

![Stock Analysis](images/dragon_curve.jpg)

## ✨ Features

### 📊 Price Summary
- Theo dõi giá và hiệu suất của 200+ cổ phiếu theo ngành
- Chỉ số tăng trưởng: 1 ngày, 1 tuần, 1 tháng, 6 tháng
- Bảng dữ liệu tương tác với heatmap màu
- Sắp xếp theo ngành và hiệu suất

### 📉 Technical Indicators
- **RSI (Relative Strength Index)**: Xác định vùng quá mua/quá bán
- **MACD**: Nhận diện xu hướng và tín hiệu giao dịch
- **Daily Calendar**: Heatmap lịch sử tăng/giảm giá

### 🔧 Data Sources
- VNDirect API (chính)
- VCI API (dự phòng)
- vnstock library

## 🚀 Quick Start

### Prerequisites
```bash
pip install pandas numpy requests vnstock matplotlib seaborn plotly openpyxl
```

### Build the Website
```bash
quarto render
```

### Preview Locally
```bash
quarto preview
```

## 📁 Project Structure

```
stockbox/
├── index.qmd                    # Trang chủ
├── RSI.qmd                      # Phân tích RSI
├── MACD.qmd                     # Phân tích MACD
├── _quarto.yml                  # Cấu hình Quarto
├── theme.scss                   # Light theme
├── theme-dark.scss              # Dark theme
└── price-summary/
    ├── Stock_price_summary.qmd  # Tổng quan giá
    ├── DailyPriceIncrease.qmd   # Calendar heatmap
    ├── utils.py                 # Helper functions
    ├── vnstock_helpers.py       # Vnstock integration
    └── vndirect.py              # VNDirect API client
```

## 🎨 UI Improvements

### Light Theme
- Modern Bootstrap Cosmo theme
- Clean typography with Atkinson Hyperlegible font
- Card-based sections with shadows
- Responsive tables with hover effects
- Color-coded percentage changes (green/red)

### Dark Theme
- GitHub-inspired dark mode
- Reduced eye strain for night trading
- Consistent color scheme across all pages

## 📊 Data Formatting

The `format_df()` function in `utils.py` provides:
- Percentage formatting with 2 decimal places
- Background gradient heatmap (-20% to +20%)
- Color coding: Red for negative, Green for positive
- Sticky headers and index for large tables
- Hover effects on rows
- Volume in millions ($X.XM)
- Price in thousands ($X,XXX)

## 🔧 Configuration

Edit `_quarto.yml` to customize:
- Site URL and repository links
- Sidebar navigation
- Theme settings
- Footer content

## 📈 Usage Examples

### Fetch Stock Data
```python
from vnstock_helpers import get_stock_data_vnstock

tickers = ['VIC', 'VHM', 'FPT']
data = get_stock_data_vnstock(tickers, start_date="2020-01-01")
```

### Calculate Returns
```python
from vnstock_helpers import calculate_returns_vnstock

returns = calculate_returns_vnstock(data)
```

### Format for Display
```python
from utils import format_df

styled_table = format_df(returns, sort_by='6m%')
```

## 🌐 Deployment

This site is deployed to GitHub Pages:
https://nguyenngocbinh.github.io/stockbox

### Deploy Commands
```bash
quarto publish gh-pages
```

## 📝 License

CC-By NguyenNgocBinh, 2023

## 🙏 Acknowledgments

- Built with [Quarto](https://quarto.org/)
- Data from [VNDirect](https://www.vndirect.com.vn/)
- Using [vnstock](https://github.com/thinh-vu/vnstock) library

---

*"Ai chiến thắng mà không hề chiến bại*  
*Ai nên khôn mà chẳng dại đôi lần"*

# 📈 Stockbox - Hộp Công Cụ Phân Tích Cổ Phiếu

Stockbox là một website được xây dựng bằng Quarto để phân tích và nghiên cứu các chỉ số kỹ thuật của thị trường chứng khoán Việt Nam.

## 🌟 Tính Năng

- **Chỉ số RSI (Relative Strength Index)**: Phân tích chỉ số sức mạnh tương đối
- **Chỉ số MACD (Moving Average Convergence Divergence)**: Phân tích đường trung bình động hội tụ phân kỳ
- **Tóm tắt giá cổ phiếu**: Theo dõi và phân tích biến động giá hàng ngày
- **Dữ liệu từ VNDirect**: Tích hợp API để lấy dữ liệu real-time

## 🚀 Cách Sử Dụng

### Yêu Cầu Hệ Thống
- Python 3.8+
- Quarto CLI

### Cài Đặt và Chạy
```bash
# Clone repository
git clone https://github.com/nguyenngocbinh/stockbox.git
cd stockbox

# Render website
quarto render

# Preview website
quarto preview
```

## 📁 Cấu Trúc Dự Án

```
stockbox/
├── index.qmd           # Trang chủ
├── RSI.qmd            # Phân tích chỉ số RSI
├── MACD.qmd           # Phân tích chỉ số MACD
├── _quarto.yml        # Cấu hình Quarto
├── price-summary/     # Thư mục phân tích giá
│   ├── Stock_price_summary.qmd
│   ├── DailyPriceIncrease.qmd
│   ├── utils.py
│   └── vndirect.py
└── images/            # Hình ảnh và biểu đồ
```

## 🌐 Truy Cập Website

Website được triển khai tại: [https://nguyenngocbinh.github.io/stockbox](https://nguyenngocbinh.github.io/stockbox)

## ⚠️ Tuyên Bố Miễn Trừ Trách Nhiệm

**QUAN TRỌNG: ĐỌC KỸ TRƯỚC KHI SỬ DỤNG**

1. **Mục đích giáo dục**: Dự án này được tạo ra chỉ với mục đích nghiên cứu, học tập và chia sẻ kiến thức về phân tích kỹ thuật. Không phải là lời khuyên đầu tư.

2. **Không phải lời khuyên tài chính**: Tất cả thông tin, phân tích và dữ liệu được cung cấp trong dự án này chỉ mang tính chất tham khảo. Chúng không cấu thành lời khuyên đầu tư, tài chính hoặc giao dịch.

3. **Rủi ro đầu tư**: Đầu tư vào thị trường chứng khoán luôn tiềm ẩn rủi ro. Bạn có thể mất một phần hoặc toàn bộ số tiền đầu tư. Quá khứ không đảm bảo cho tương lai.

4. **Tự chịu trách nhiệm**: Mọi quyết định đầu tư dựa trên thông tin từ dự án này hoàn toàn là trách nhiệm của bạn. Tác giả không chịu trách nhiệm về bất kỳ tổn thất nào phát sinh.

5. **Độ chính xác dữ liệu**: Mặc dù cố gắng cung cấp thông tin chính xác, chúng tôi không đảm bảo tính đầy đủ, chính xác hoặc cập nhật của dữ liệu.

6. **Tư vấn chuyên nghiệp**: Trước khi đưa ra bất kỳ quyết định đầu tư nào, hãy tham khảo ý kiến của các chuyên gia tài chính có chứng chỉ hành nghề.

## 🤝 Đóng Góp

Chúng tôi hoan nghênh mọi đóng góp! Vui lòng:
1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 💖 Hỗ Trợ

Nếu bạn thấy dự án này hữu ích và muốn ủng hộ việc phát triển, hãy cân nhắc mua tôi một ly cà phê!

<a href="https://www.buymeacoffee.com/nguyenngocbinh" target="_blank"><img src="https://img.buymeacoffee.com/button-api/?text=Mua cho tôi ly cà phê&emoji=☕&slug=nguyenngocbinh&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"></a>

## 📝 Giấy Phép Sử Dụng

Dự án này được phân phối dưới Giấy phép MIT. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

### Giấy Phép MIT - Tóm Tắt

✅ **Được phép:**
- Sử dụng thương mại
- Chỉnh sửa
- Phân phối
- Sử dụng cá nhân

❌ **Điều kiện:**
- Phải bao gồm thông báo bản quyền và giấy phép trong tất cả các bản sao
- Tác giả không chịu trách nhiệm về bất kỳ thiệt hại nào

📧 **Liên Hệ**: [nguyenngocbinh@gmail.com](mailto:nguyenngocbinh@gmail.com)

---

⭐ **Nếu dự án này hữu ích, hãy cho chúng tôi một ngôi sao trên GitHub!**

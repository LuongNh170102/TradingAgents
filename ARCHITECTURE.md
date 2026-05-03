# TradingAgents Crypto — Kiến Trúc Hệ Thống Tổng Thể

## Mục tiêu

TradingAgents Crypto là một hệ thống hỗ trợ quyết định giao dịch crypto theo hướng **research first, trade second**.

- Nhận dữ liệu thị trường từ Binance và các nguồn phụ trợ
- Phát hiện setup tiềm năng bằng scanner
- Phân tích sâu để tạo signal
- Lưu toàn bộ kết quả vào memory theo tầng
- Chỉ dùng lesson đã lọc để phục vụ trade mode

---

## Nguyên tắc thiết kế

1. **Human luôn là người quyết định cuối cùng**
2. **Không dùng raw memory trực tiếp để ra quyết định trade**
3. **Tất cả mode đều ghi vào raw memory trước**
4. **Lesson chỉ được tạo sau khi lọc và tổng hợp**
5. **Trade mode chỉ đọc global lesson memory**
6. **Kiến trúc phải đơn giản, dễ debug, dễ mở rộng**

---

## Kiến trúc tổng quát

Hệ thống gồm 4 khối chính:

1. **Scanner**: quét thị trường và tìm setup đáng chú ý
2. **Analyzer**: phân tích sâu setup đã được trigger
3. **Memory Pipeline**: lưu raw, lọc lesson, đẩy lên global
4. **Execution / Notification**: gửi signal và vào lệnh khi có xác nhận

```text
Market Data → Scanner → Analyzer → Telegram → Human Confirm → Executor
                      ↘
                       Raw Memory → Lesson Processor → Global Memory → Trade Mode
```

---

## 2 mode vận hành

### Training mode

Mục đích:
- chạy không dùng tiền thật
- tạo dữ liệu
- lưu raw case
- hỗ trợ tạo lesson
- ưu tiên học và quan sát

### Trade mode

Mục đích:
- dùng tiền thật
- trade theo signal đã được lọc
- chỉ đọc global lesson memory
- ưu tiên an toàn và kỷ luật rủi ro

### Quan hệ giữa hai mode

- Training mode tạo nhiều dữ liệu hơn
- Trade mode dùng lesson đã lọc để ra quyết định
- Hai mode có thể chạy song song nhưng **không được trộn logic quyết định**

---

## Memory architecture

### 1) Raw memory

Raw memory lưu **toàn bộ log gốc** từ mọi mode.

Nội dung có thể gồm:
- thời gian
- mode
- strategy
- timeframe
- coin
- signal
- entry / exit
- result
- context thị trường
- reasoning
- notes

Raw memory có nhiệm vụ:
- audit
- debug
- truy vết
- làm nguồn dữ liệu cho xử lý tiếp theo

**Raw memory không dùng trực tiếp để trade.**

### 2) Lesson memory

Lesson memory là phần đã được xử lý từ raw.

Một lesson chỉ nên được tạo khi:
- có đủ số lượng case
- pattern khá rõ
- kết quả ổn định
- không còn quá nhiều noise

Lesson memory lưu:
- pattern
- điều kiện kích hoạt
- kết luận
- khuyến nghị
- confidence
- số lượng case chứng minh

### 3) Global memory

Global memory là tập hợp các lesson đã lọc và chuẩn hóa.

Đây là tầng mà:
- trade mode đọc chính
- các mode khác có thể tham khảo
- dùng để tạo prompt / context / reflection

### Luồng memory chuẩn

```text
All modes
   ↓
Raw memory
   ↓
Memory processor
   ↓
Lesson memory
   ↓
Global memory
   ↓
Trade mode reads here
```

---

## Tại sao phải tách memory

Nếu gộp chung raw và lesson quá sớm, hệ thống có thể học nhầm.

Ví dụ:
- `td1` vào lệnh SELL sai ở một bối cảnh xấu
- `tr2` vào lệnh BUY đúng trong bối cảnh khác
- nếu gộp không có nhãn rõ ràng, trade mode có thể rút ra kết luận sai cho cả chiến lược

Tách memory giúp:
- không học lẫn giữa các mode
- không biến một case thua thành kết luận chung
- dễ kiểm tra hiệu quả từng strategy / timeframe / mode
- giảm nhiễu trước khi lên quyết định trade

---

## Memory processor

Memory processor là service xử lý raw thành lesson.

Nhiệm vụ chính:
1. đọc raw logs
2. chuẩn hóa dữ liệu
3. group theo strategy / timeframe / regime / direction
4. loại duplicate và noise
5. tính thống kê cơ bản
6. tạo lesson nếu đủ bằng chứng
7. đẩy lesson tốt lên global

### Cách xử lý hợp lý

- **Rule-based** để gom pattern ban đầu
- **Thống kê** để đánh giá độ tin cậy
- **LLM / model free** để tóm tắt và viết lesson
- **Human review** nếu lesson ảnh hưởng trade thật

### Mẫu rule đơn giản

- cùng strategy
- cùng timeframe
- cùng regime
- cùng direction
- cùng outcome pattern

### Khi nào tạo lesson

Nên có ngưỡng tối thiểu, ví dụ:
- đủ số lượng case
- win/loss lệch rõ
- confidence vượt ngưỡng

---

## Dữ liệu memory mẫu

### Raw record

```json
{
  "trade_id": "BTC_20250115_001",
  "mode_id": "td1",
  "strategy": "breakout",
  "timeframe": "5m",
  "coin": "BTC/USDT",
  "signal": "BUY",
  "entry": 67000,
  "exit": 64000,
  "result": "LOSS",
  "pnl": -3.0,
  "market_context": {
    "rsi": 27,
    "volume_spike": 2.3,
    "fear_greed": 25,
    "news": "Fed meeting tomorrow"
  },
  "reasoning": "RSI oversold, reversal expected",
  "reflection_candidate": "Avoid BUY signals 24h before Fed meetings regardless of RSI",
  "memory_tier": "raw"
}
```

### Lesson record

```json
{
  "lesson_id": "lesson_0007",
  "strategy": "breakout",
  "timeframe": "5m",
  "condition": {
    "market_regime": "sideway",
    "volume": "low"
  },
  "lesson": "Breakout trades in low-volume sideways markets have a high failure rate.",
  "recommendation": "Avoid opening new breakout positions unless volume confirms momentum.",
  "confidence": 0.86,
  "evidence_count": 27,
  "source_modes": ["td1", "tr2"],
  "memory_tier": "global"
}
```

---

## Scanner và Analyzer

### Scanner

Scanner có nhiệm vụ:
- quét coin theo timeframe ngắn
- tính indicators cơ bản
- tìm tín hiệu đủ mạnh để trigger analyzer
- giảm số lần gọi phân tích sâu

### Analyzer

Analyzer có nhiệm vụ:
- tổng hợp technical / sentiment / news / macro
- tạo signal có cấu trúc rõ ràng
- đẩy output sang Telegram
- ghi log vào raw memory

---

## Notification flow

### Telegram bot

Telegram bot chỉ là lớp trung gian để:
- gửi signal
- nhận confirm / skip
- theo dõi trạng thái lệnh

Bot không nên chứa logic quyết định chính.

### Executor

Executor chỉ chạy khi đã có confirm từ người dùng.

Quy trình:
1. nhận confirm
2. kiểm tra balance
3. tính size
4. đặt lệnh
5. đặt TP/SL
6. monitor kết quả
7. ghi kết quả vào raw memory

---

## Cấu trúc thư mục đề xuất

```text
tradingagents/
├── scanner/
│   └── fast_scanner.py
├── analyzer/
│   └── deep_analyzer.py
├── execution/
│   └── binance_executor.py
├── notifications/
│   └── telegram_bot.py
├── memory/
│   ├── raw/
│   ├── lessons/
│   ├── global/
│   ├── memory_processor.py
│   └── trade_memory.py
├── dataflows/
│   ├── ccxt_provider.py
│   ├── coingecko_provider.py
│   └── indicators.py
├── config/
│   └── trading_config.py
└── main.py
```

---

## Cách dùng memory theo mode

### Tất cả mode
- đều ghi vào raw memory

### Training mode
- tạo nhiều raw case
- ưu tiên exploration
- hỗ trợ sinh lesson

### Trade mode
- chỉ đọc global lesson
- không tự suy luận từ raw
- ưu tiên ổn định và an toàn

---

## Những phần không cần thiết đã lược bỏ

Để architecture gọn hơn, file này **không đi sâu** vào:
- danh sách model cụ thể
- chi phí API chi tiết
- roadmap theo tuần/tháng
- format Telegram quá dài
- cấu hình từng service nhỏ

Các phần đó có thể chuyển sang file config hoặc tài liệu triển khai riêng.

---

## Kết luận

Kiến trúc nên đi theo hướng:

- **Scanner để phát hiện setup**
- **Analyzer để đánh giá sâu**
- **Raw memory để lưu tất cả**
- **Lesson processor để lọc và chuẩn hóa**
- **Global memory để phục vụ trade mode**
- **Human quyết định cuối cùng**

Mục tiêu lớn nhất là:
> **không để bot học sai từ dữ liệu rác, và không để trade mode dùng raw case trực tiếp.**

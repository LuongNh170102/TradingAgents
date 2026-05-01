# TradingAgents Crypto — Kiến Trúc Hệ Thống Tổng Thể

## Tổng quan

- **Tên dự án:** TradingAgents Crypto (Fork từ TradingAgents)
- **Mục tiêu:** Research Bot hỗ trợ quyết định giao dịch crypto
- **Người dùng:** Cá nhân tại Việt Nam
- **Exchange:** Binance (qua CCXT + python-binance)
- **Output:** Telegram signal → Human confirm → Vào lệnh

---

## Kiến Trúc 2 Lớp

### LỚP 1: Fast Scanner (Chạy mỗi 15 phút, 24/7)

**Mục đích:** Scan nhanh toàn bộ coins đầu vào, tính toán indicators cơ bản, lọc tín hiệu đáng chú ý để trigger Lớp 2.

**Input:**
- Danh sách coins: BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, XRP/USDT
- Timeframe: 15 phút
- Số nến lấy: 100 nến gần nhất (từ Binance qua CCXT)

**Indicators tính toán:**
- RSI (14): Oversold < 28, Overbought > 72
- MACD: Golden cross / Death cross
- Bollinger Bands: Squeeze release, giá chạm dải trên/dưới
- Volume Spike: Volume hiện tại > 2x trung bình 20 nến
- EMA Crossover: EMA 9 cắt EMA 21
- Support/Resistance Break: Giá phá vỡ vùng SR quan trọng

**Điều kiện trigger Lớp 2:**
- Ít nhất 2/6 indicators có tín hiệu cùng lúc
- Coin đó chưa được trigger trong 4 giờ qua (cooldown)
- Tín hiệu xuất hiện ít nhất 2 nến liên tiếp (tránh false signal)
- Không có lệnh đang mở với coin đó

**Output:**
- Không có tín hiệu → bỏ qua, chờ 15 phút tiếp
- Có tín hiệu → trigger Lớp 2 kèm context (coin, lý do, giá trị indicators)

---

### LỚP 2: TradingAgents Deep Analysis (Chỉ chạy khi được Lớp 1 trigger)

**Mục đích:** Phân tích sâu toàn diện (kỹ thuật + tin tức + sentiment + macro) để đưa ra signal chất lượng cao.

#### Data Collectors

| Nguồn | Dữ liệu lấy | Thư viện |
|-------|-------------|----------|
| Binance (CCXT) | OHLCV chart, render PNG | ccxt, mplfinance |
| CoinGecko | Price, Market Cap, Volume, Trending | pycoingecko |
| Reddit | Sentiment cộng đồng crypto | praw |
| Fear & Greed Index | Tâm lý thị trường tổng thể | requests |
| FRED | Macro: Fed rate, CPI, DXY | fredapi |

#### Multi-Agent Pipeline

```
Market Analyst      → DeepSeek R1        (phân tích kỹ thuật, logic toán)
News Analyst        → Claude Sonnet      (đọc hiểu tin tức, ngữ cảnh)
Sentiment Analyst   → DeepSeek Chat      (phân tích tâm lý cộng đồng)
Chart Analyst       → GPT-4o Vision      (đọc chart PNG, nhận dạng pattern)
Fundamentals        → DeepSeek Chat      (on-chain, tokenomics)
        ↓
Bull Researcher     → DeepSeek R1        (lập luận lý do MUA)
Bear Researcher     → DeepSeek R1        (lập luận lý do BÁN)
Research Manager    → DeepSeek R1        (tổng hợp bull/bear)
        ↓
Risk Team           → Gemini 2.5 Pro     (đánh giá rủi ro, context dài)
Portfolio Manager   → DeepSeek R1        (quyết định cuối cùng)
```

#### Memory System

- **Short-term Memory:** Lệnh đang mở, signal vừa phát, context thị trường hôm nay
- **Long-term Memory:** Lịch sử toàn bộ lệnh, win/loss record, pattern hay thắng/thua
- **Reflection Memory:** Sau mỗi lệnh thua → AI tự phân tích "tại sao sai" → lưu bài học → áp dụng lần sau

**Cấu trúc dữ liệu lưu mỗi lệnh:**

```json
{
  "trade_id": "BTC_20250115_001",
  "coin": "BTC-USD",
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
  "ai_reasoning": "RSI oversold, reversal expected",
  "reflection": "Sai vì không chú ý Fed meeting. RSI oversold không đủ khi có macro event lớn",
  "lesson": "Avoid BUY signals 24h before Fed meetings regardless of RSI"
}
```

#### Output Signal Format

```
coin:        BTC/USDT
action:      MUA / BÁN / HOLD
entry:       $67,000
target_tp:   $71,000 (+6.0%)
stop_loss:   $65,000 (-3.0%)
rr_ratio:    1:2
confidence:  72%
technical:   Bullish
news:        Neutral
fear_greed:  25 (Fear)
bull_case:   [lý do chi tiết tại sao nên mua]
bear_case:   [lý do chi tiết tại sao nên bán]
trigger_by:  RSI=27, Volume spike 2.3x
```

---

### TELEGRAM BOT

**Mục đích:** Nhận output từ Lớp 2, format đẹp, push đến điện thoại, nhận confirm từ user.

**Format tin nhắn:**

```
⚡ BTC/USDT SIGNAL
Trigger: RSI=27, Volume spike 2.3x

🟢 Action:     MUA
📌 Entry:      $67,000
🎯 Target:     $71,000 (+6.0%)
🛑 Stop Loss:  $65,000 (-3.0%)
⚖️ R:R Ratio:  1:2
🎲 Confidence: 72%

📊 Technical:  Bullish
📰 News:       Neutral
😱 Fear&Greed: 25 / Fear

💚 Bull case: [lý do mua]
🔴 Bear case: [lý do cẩn thận]

[✅ Vào lệnh]  [❌ Skip]
```

**Các lệnh bot hỗ trợ:**
- `/status` — Xem các lệnh đang mở
- `/summary` — Báo cáo ngày hôm nay
- `/pnl` — Thống kê lời/lỗ tổng
- `/pause` — Tạm dừng scanner
- `/resume` — Tiếp tục scanner

---

### BINANCE EXECUTOR

**Mục đích:** Nhận signal đã được user confirm, tự động vào lệnh trên Binance.

**Quy trình:**
1. Nhận confirm ✅ từ Telegram
2. Kiểm tra balance đủ không
3. Tính size lệnh (2% vốn / risk per trade)
4. Đặt LIMIT ORDER tại giá entry
5. Set Take Profit (OCO order)
6. Set Stop Loss (OCO order)
7. Monitor lệnh → báo cáo khi đóng
8. Lưu kết quả vào Memory System

**Bảo mật API Key Binance:**
- Chỉ cấp quyền: Trade (Enable Spot & Margin Trading)
- KHÔNG cấp quyền: Withdraw
- Whitelist IP của VPS
- Lưu trong file `.env`, không commit lên GitHub

---

## Cấu Trúc Thư Mục

```
tradingagents/
├── scanner/
│   ├── __init__.py
│   └── fast_scanner.py          # Lớp 1: scan + indicators + filter
│
├── scheduler/
│   ├── __init__.py
│   └── scheduler.py             # APScheduler chạy 24/7
│
├── dataflows/
│   ├── ccxt_provider.py         # Lấy OHLCV từ Binance + render chart
│   ├── coingecko_provider.py    # Market data từ CoinGecko
│   ├── indicators.py            # RSI, MACD, BB, Volume, EMA, SR
│   └── ... (existing files)
│
├── notifications/
│   ├── __init__.py
│   └── telegram_bot.py          # Push signal + inline buttons
│
├── execution/
│   ├── __init__.py
│   └── binance_executor.py      # Đặt lệnh Binance sau khi confirm
│
├── memory/
│   ├── trade_memory.py          # Lưu lịch sử + reflection
│   └── ... (existing files)
│
├── config/
│   └── trading_config.py        # Cấu hình coins, timeframe, risk...
│
├── .env                         # API keys (không commit)
├── .env.example                 # Template .env
├── requirements.txt
└── main.py                      # Entry point khởi động hệ thống
```

---

## Cấu Hình Hệ Thống (trading_config.py)

```python
TRADING_CONFIG = {
    # Coins cần scan
    "coins": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"],

    # Timeframe
    "scan_timeframe": "15m",          # Lớp 1 scan
    "analysis_timeframe": "4h",       # Lớp 2 phân tích
    "chart_timeframes": ["4h", "1d"], # Chart gửi cho Vision model

    # Scanner settings
    "scan_interval_minutes": 15,      # Chạy Lớp 1 mỗi 15 phút
    "ohlcv_limit": 100,               # Số nến lấy
    "min_conditions_trigger": 2,      # Số điều kiện tối thiểu
    "cooldown_hours": 4,              # Cooldown mỗi coin
    "confirm_candles": 2,             # Số nến confirm tín hiệu

    # Indicator thresholds
    "rsi_oversold": 28,
    "rsi_overbought": 72,
    "volume_spike_multiplier": 2.0,

    # Risk management
    "risk_per_trade_pct": 2.0,        # % vốn risk mỗi lệnh
    "min_rr_ratio": 2.0,              # R:R tối thiểu 1:2
    "max_open_trades": 5,             # Số lệnh mở cùng lúc tối đa

    # Model assignment
    "models": {
        "market_analyst":     "deepseek-reasoner",
        "news_analyst":       "claude-3-5-sonnet-20241022",
        "sentiment_analyst":  "deepseek-chat",
        "chart_analyst":      "gpt-4o",
        "fundamentals":       "deepseek-chat",
        "bull_researcher":    "deepseek-reasoner",
        "bear_researcher":    "deepseek-reasoner",
        "risk_team":          "gemini-2.5-pro",
        "portfolio_manager":  "deepseek-reasoner",
    },

    # Schedule báo cáo cố định
    "daily_reports": ["07:00", "21:00"],  # Báo cáo sáng + tối
}
```

---

## Biến Môi Trường (.env)

```
# LLM APIs
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key

# Exchange
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret

# Data
COINGECKO_API_KEY=your_coingecko_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
FRED_API_KEY=your_fred_key

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Cấu hình
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Chi Phí Vận Hành

| Dịch vụ | Chi phí/tháng | Ghi chú |
|---------|---------------|---------|
| VPS (Contabo/Vultr) | $6-10 | Ubuntu 22.04, 2GB RAM |
| DeepSeek API | $10-20 | Main LLM, rẻ nhất |
| Claude API | $5-10 | News Analyst |
| GPT-4o API | $5-10 | Chart Vision |
| Gemini API | $3-5 | Risk Team |
| CoinGecko | $0 | Free tier đủ dùng |
| Reddit API | $0 | Free |
| Telegram Bot | $0 | Free |
| python-binance | $0 | Free |
| **TỔNG** | **~$29-55** | |

---

## Lộ Trình Thực Hiện

### Tuần 1-2: Foundation
- [ ] Merge PR hiện tại vào main
- [ ] Viết `ccxt_provider.py` — kết nối Binance, lấy OHLCV, render chart PNG
- [ ] Viết `indicators.py` — RSI, MACD, Bollinger, Volume, EMA, SR
- [ ] Test thủ công với BTC/ETH

### Tuần 3-4: Lớp 1 Automation
- [ ] Viết `fast_scanner.py` — scan tất cả coins, apply filter
- [ ] Viết `scheduler.py` — APScheduler chạy mỗi 15 phút
- [ ] Test trigger logic (log ra terminal)

### Tháng 2: Communication Layer
- [ ] Viết `coingecko_provider.py` — market data
- [ ] Viết `telegram_bot.py` — push signal + inline buttons ✅❌
- [ ] Test end-to-end: Scanner → TradingAgents → Telegram
- [ ] Vào lệnh tay trên Binance (chưa dùng executor)

### Tháng 3: Execution Layer
- [ ] Viết `binance_executor.py` — đặt lệnh sau khi confirm
- [ ] Chạy thật với vốn nhỏ (1-2 triệu VND)
- [ ] Track kết quả, validate win rate thực tế

### Tháng 4+: Optimization
- [ ] Nâng cấp `trade_memory.py` — reflection learning
- [ ] Tinh chỉnh indicator thresholds dựa trên dữ liệu thực
- [ ] Thêm coins mới nếu muốn
- [ ] Tăng vốn khi đã validate hệ thống

---

## Nguyên Tắc Quan Trọng

### 1. Human Always In Control
- AI nghiên cứu và đề xuất, Human quyết định cuối cùng
- Không bao giờ để chạy full auto không giám sát

### 2. Start Small
- Bắt đầu với 1-2 triệu VND
- Tăng vốn chỉ sau khi validate hệ thống ít nhất 1-2 tháng

### 3. Risk Management nghiêm ngặt
- Stop loss LUÔN được đặt cho mọi lệnh
- Tối đa 2% vốn risk mỗi lệnh
- Tối đa 3-5 lệnh mở cùng lúc
- R:R tối thiểu 1:2

### 4. Luôn dùng LIMIT ORDER
- Không dùng MARKET ORDER
- Tránh slippage, vào lệnh tại giá mong muốn

### 5. Track Everything
- Ghi lại tất cả lệnh kể cả lệnh skip
- Review performance hàng tuần
- AI học từ sai lầm để cải thiện

---

## Kỳ Vọng Thực Tế

| Kịch bản | Return/tháng | Điều kiện |
|----------|-------------|-----------|
| Thận trọng | 8-15% | Thị trường bình thường, follow system |
| Thực tế | 15-25% | Thị trường tốt, hệ thống ổn định |
| Lạc quan | 25-35% | Bull market, mọi thứ hoạt động tốt |
| Tệ nhất | -10% đến -30% | Black swan, crypto crash đột ngột |

**Win rate mục tiêu:** 60-65% với R:R 1:2 → Expected Value dương dài hạn

> **Lưu ý:** Đây là công cụ hỗ trợ quyết định, không phải đảm bảo lợi nhuận. Chỉ đầu tư vốn nhàn rỗi, không vay mượn.

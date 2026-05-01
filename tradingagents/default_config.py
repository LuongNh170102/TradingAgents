import os
import tempfile
from pathlib import Path

_TRADINGAGENTS_HOME = os.path.join(os.path.expanduser("~"), ".tradingagents")
def get_default_cache_dir() -> str:
    """Return a writable cache directory across local and Docker environments."""

    env_path = os.getenv("TRADINGAGENTS_CACHE_DIR")
    if env_path:
        return env_path

    candidate = Path(_TRADINGAGENTS_HOME) / "cache"

    try:
        candidate.mkdir(parents=True, exist_ok=True)
        test_file = candidate / ".write_test"
        test_file.touch(exist_ok=True)
        test_file.unlink(missing_ok=True)
        return str(candidate)
    except Exception:
        pass

    fallback = Path(tempfile.gettempdir()) / "tradingagents" / "cache"
    fallback.mkdir(parents=True, exist_ok=True)
    return str(fallback)


DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.join(_TRADINGAGENTS_HOME, "logs")),
    "data_cache_dir": get_default_cache_dir(),
    "memory_log_path": os.getenv("TRADINGAGENTS_MEMORY_LOG_PATH", os.path.join(_TRADINGAGENTS_HOME, "memory", "trading_memory.md")),
    # Optional cap on the number of resolved memory log entries. When set,
    # the oldest resolved entries are pruned once this limit is exceeded.
    # Pending entries are never pruned. None disables rotation entirely.
    "memory_log_max_entries": None,
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.4",
    "quick_think_llm": "gpt-5.4-mini",
    # When None, each provider's client falls back to its own default endpoint
    # (api.openai.com for OpenAI, generativelanguage.googleapis.com for Gemini, ...).
    # The CLI overrides this per provider when the user picks one. Keeping a
    # provider-specific URL here would leak (e.g. OpenAI's /v1 was previously
    # being forwarded to Gemini, producing malformed request URLs).
    "backend_url": None,
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    "anthropic_effort": None,           # "high", "medium", "low"
    # Checkpoint/resume: when True, LangGraph saves state after each node
    # so a crashed run can resume from the last successful step.
    "checkpoint_enabled": False,
    # Output language for analyst reports and final decision
    # Internal agent debate stays in English for reasoning quality
    "output_language": "English",
    # Benchmark used for alpha calculation in deferred reflection.
    # When `benchmark_ticker` is set, it wins for every analysis.
    # Otherwise the longest matching suffix in `benchmark_map` is used,
    # falling back to the "" entry for tickers without a known suffix.
    "benchmark_ticker": None,
    "benchmark_map": {
        ".NS": "^NSEI",     # Nifty 50 (NSE India)
        ".BO": "^BSESN",    # Sensex (BSE India)
        ".T":  "^N225",     # Nikkei 225 (Japan)
        ".HK": "^HSI",      # Hang Seng (Hong Kong)
        ".L":  "^FTSE",     # FTSE 100 (London)
        ".TO": "^GSPTSE",   # TSX Composite (Toronto)
        "":    "SPY",       # default for US-listed tickers
    },
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # ── News / data fetching parameters ───────────────────────────────────
    # Maximum number of articles fetched per ticker (ticker-specific news).
    # Increase for longer lookback strategies; decrease to reduce token usage.
    "news_article_limit": 20,
    # Number of days to look back when fetching ticker-specific news.
    "news_lookback_days": 7,
    # Maximum number of articles fetched for global/macro news.
    "global_news_article_limit": 10,
    # Number of days to look back for global/macro news.
    "global_news_lookback_days": 7,
    # Search queries used by get_global_news to pull macro headlines.
    # Extend or replace this list to broaden geographic/sector coverage.
    "global_news_queries": [
        "Federal Reserve interest rates inflation",
        "S&P 500 earnings GDP economic outlook",
        "geopolitical risk trade war sanctions",
        "ECB Bank of England BOJ central bank policy",
        "oil commodities supply chain energy",
    ],
    # ──────────────────────────────────────────────────────────────────────
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: alpha_vantage, yfinance
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance
        "fundamental_data": "yfinance",      # Options: alpha_vantage, yfinance
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
}

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib
import yfinance as yf  # type: ignore
from pathlib import Path
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs):
        return None
import os
import math
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from supabase import create_client
except ModuleNotFoundError:
    create_client = None

try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:
    ARIMA = None


app = Flask(__name__)
CORS(app)

load_dotenv(Path(__file__).resolve().parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = (
    os.getenv("SUPABASE_SECRET_KEY")
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
)

supabase = None
supabase_error = None

if create_client is None:
    supabase_error = "Supabase package is not installed. Run: python3 -m pip install supabase"
elif not SUPABASE_URL or not SUPABASE_KEY:
    supabase_error = "Supabase env vars are missing. Add SUPABASE_URL and SUPABASE_SECRET_KEY to backend/.env."
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as error:
        supabase_error = str(error)


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "stock_direction_model.pkl"
FEATURES_PATH = BASE_DIR / "models" / "features.pkl"


def resolve_symbol(query):
    clean = str(query or "").strip()
    if "(" in clean and ")" in clean:
        inside = clean.split("(")[-1].split(")")[0]
        if inside:
            clean = inside
    return "".join(ch for ch in clean.upper() if ch.isalpha() or ch == "." or ch == "-")


try:
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
except Exception as e:
    print("Error loading model files:", e)
    model = None
    features = None


def backend_ready():
    return model is not None and features is not None


def supabase_ready():
    return supabase is not None


def format_price(value):
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def format_percent(value):
    if value is None or pd.isna(value):
        return None
    return round(float(value) * 100, 2)


def safe_int(value):
    if value is None or pd.isna(value):
        return None
    return int(value)


def calculate_risk_level(confidence, volatility):
    if volatility is None or pd.isna(volatility):
        return "Medium", "Risk is estimated as medium because volatility data is limited."

    if confidence >= 75 and volatility < 3:
        return "Low", "The model has higher confidence and recent volatility is relatively low."
    elif confidence >= 60 and volatility < 6:
        return "Medium", "The model has moderate confidence or the stock has some recent volatility."
    else:
        return "High", "The model has lower confidence or the stock has higher recent volatility."


def get_yfinance_data(ticker, period="180d"):
    ticker = resolve_symbol(ticker)

    if not ticker:
        return None, None

    stock = yf.Ticker(ticker)
    history = stock.history(period=period, interval="1d")

    if history.empty:
        return None, None

    history = history.reset_index()

    if "Date" not in history.columns:
        history.rename(columns={"Datetime": "Date"}, inplace=True)

    history["Date"] = pd.to_datetime(history["Date"]).dt.tz_localize(None)
    history["Ticker"] = ticker
    history = history[["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]]

    return stock, history


def add_model_features(stock_data):
    stock_data = stock_data.copy()
    stock_data = stock_data.sort_values("Date")

    stock_data["Daily_Return"] = stock_data["Close"].pct_change()
    stock_data["MA_5"] = stock_data["Close"].rolling(window=5).mean()
    stock_data["MA_10"] = stock_data["Close"].rolling(window=10).mean()
    stock_data["Volume_Change"] = stock_data["Volume"].pct_change()
    stock_data["Volatility_5"] = stock_data["Close"].rolling(window=5).std()

    return stock_data


def get_company_name(stock, fallback="Company name unavailable"):
    try:
        info = stock.info
        return info.get("longName") or info.get("shortName") or fallback
    except Exception:
        return fallback


def get_latest_valid_row(stock_data):
    if not features:
        return None

    clean_data = stock_data.dropna(subset=features)

    if clean_data.empty:
        return None

    return clean_data.iloc[-1]


def history_to_json(stock_data, rows=60):
    stock_data = stock_data.sort_values("Date").tail(rows)
    history = []

    for _, row in stock_data.iterrows():
        history.append({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "open": format_price(row["Open"]),
            "high": format_price(row["High"]),
            "low": format_price(row["Low"]),
            "close": format_price(row["Close"]),
            "volume": safe_int(row["Volume"])
        })

    return history


def next_market_dates(last_date, days):
    dates = []
    current = pd.Timestamp(last_date)

    while len(dates) < days:
        current = current + pd.Timedelta(days=1)
        if current.weekday() < 5:
            dates.append(current)

    return dates


def fallback_forecast(close_series, future_dates):
    returns = close_series.pct_change().dropna()
    recent_returns = returns.tail(30)
    drift = float(recent_returns.mean()) if not recent_returns.empty else 0.0
    volatility = float(recent_returns.std()) if len(recent_returns) > 1 else 0.015

    if math.isnan(drift):
        drift = 0.0
    if math.isnan(volatility) or volatility <= 0:
        volatility = 0.015

    last_price = float(close_series.iloc[-1])
    forecast = []

    for step, date in enumerate(future_dates, start=1):
        predicted = last_price * ((1 + drift) ** step)
        spread = 1.96 * volatility * math.sqrt(step) * predicted
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "predicted_close": format_price(predicted),
            "lower": format_price(max(predicted - spread, 0)),
            "upper": format_price(predicted + spread)
        })

    return forecast, "Drift forecast"


def arima_forecast(close_series, future_dates):
    if ARIMA is None or len(close_series) < 40:
        return fallback_forecast(close_series, future_dates)

    try:
        fitted = ARIMA(close_series.astype(float), order=(2, 1, 2)).fit()
        result = fitted.get_forecast(steps=len(future_dates))
        predicted = result.predicted_mean
        conf_int = result.conf_int(alpha=0.05)
        forecast = []

        for i, date in enumerate(future_dates):
            lower = float(conf_int.iloc[i, 0])
            upper = float(conf_int.iloc[i, 1])
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_close": format_price(predicted.iloc[i]),
                "lower": format_price(max(lower, 0)),
                "upper": format_price(max(upper, 0))
            })

        return forecast, "ARIMA(2,1,2)"
    except Exception:
        return fallback_forecast(close_series, future_dates)


def build_forecast(ticker, days=10):
    days = max(1, min(int(days), 30))
    ticker = resolve_symbol(ticker)
    stock, stock_data = get_yfinance_data(ticker, period="1y")

    if stock_data is None:
        return None, {
            "error": "Ticker not found or no data returned from yfinance.",
            "ticker": ticker
        }, 404

    stock_data = stock_data.sort_values("Date")
    history = history_to_json(stock_data, rows=90)
    close_series = stock_data["Close"].dropna().astype(float)
    future_dates = next_market_dates(stock_data.iloc[-1]["Date"], days)
    forecast, model_name = arima_forecast(close_series, future_dates)
    last_close = float(close_series.iloc[-1])
    final_prediction = forecast[-1]["predicted_close"] if forecast else last_close
    expected_change = ((final_prediction - last_close) / last_close) * 100 if last_close else 0
    avg_interval = None

    if forecast:
        widths = [
            row["upper"] - row["lower"]
            for row in forecast
            if row["upper"] is not None and row["lower"] is not None
        ]
        if widths:
            avg_interval = sum(widths) / len(widths)

    return {
        "ticker": ticker,
        "company_name": get_company_name(stock, ticker),
        "forecast_model": model_name,
        "history": history,
        "forecast": forecast,
        "forecast_days": days,
        "last_close": format_price(last_close),
        "expected_change_percent": round(expected_change, 2),
        "average_confidence_interval_width": format_price(avg_interval),
        "data_source": "Yahoo Finance via yfinance",
        "note": "Forecasts are educational time-series estimates, not financial advice."
    }, None, None


def search_yfinance(query):
    query = str(query or "").strip()
    if not query:
        return []

    results = []

    try:
        params = urlencode({
            "q": query,
            "quotesCount": 8,
            "newsCount": 0,
            "enableFuzzyQuery": "true"
        })
        request = Request(
            f"https://query1.finance.yahoo.com/v1/finance/search?{params}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload.get("quotes", []):
            symbol = item.get("symbol")
            name = item.get("longname") or item.get("shortname") or symbol
            quote_type = item.get("quoteType")
            if symbol and quote_type in (None, "EQUITY", "ETF"):
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": item.get("exchange") or item.get("exchDisp") or ""
                })
    except Exception:
        pass

    try:
        search = yf.Search(query, max_results=8)
        quotes = getattr(search, "quotes", []) or []
        for item in quotes:
            symbol = item.get("symbol") or item.get("ticker")
            name = item.get("longname") or item.get("shortname") or item.get("name")
            quote_type = item.get("quoteType") or item.get("typeDisp")
            if symbol and quote_type in (None, "EQUITY", "ETF"):
                results.append({
                    "symbol": symbol,
                    "name": name or symbol,
                    "exchange": item.get("exchange") or item.get("exchDisp") or ""
                })
    except Exception:
        pass

    if not results:
        ticker = resolve_symbol(query)
        if ticker:
            stock, stock_data = get_yfinance_data(ticker, period="5d")
            if stock_data is not None:
                results.append({
                    "symbol": ticker,
                    "name": get_company_name(stock, ticker),
                    "exchange": ""
                })

    seen = set()
    unique_results = []
    for result in results:
        if result["symbol"] in seen:
            continue
        seen.add(result["symbol"])
        unique_results.append(result)

    return unique_results[:8]


@app.route("/")
def home():
    return jsonify({
        "app": "StockSensei Backend",
        "status": "running",
        "data_source": "Yahoo Finance through yfinance",
        "routes": [
            "/health",
            "/search/<query>",
            "/live/<ticker>",
            "/history/<ticker>",
            "/predict/<ticker>",
            "/forecast/<ticker>?days=10"
        ],
        "note": "For educational use only. Not financial advice."
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok" if backend_ready() else "error",
        "model_loaded": model is not None,
        "features_loaded": features is not None,
        "supabase_ready": supabase_ready(),
        "supabase_error": None if supabase_ready() else supabase_error,
        "forecast_model_available": "ARIMA" if ARIMA is not None else "drift fallback",
        "data_source": "yfinance"
    })


@app.route("/search/<query>")
def search(query):
    return jsonify({
        "query": query,
        "results": search_yfinance(query),
        "data_source": "Yahoo Finance via yfinance"
    })


@app.route("/resolve/<query>")
def resolve_query(query):
    results = search_yfinance(query)
    ticker = results[0]["symbol"] if results else resolve_symbol(query)
    return jsonify({
        "query": query,
        "ticker": ticker,
        "results": results
    })


@app.route("/live/<ticker>")
def live_summary(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Model files are not loaded correctly."
        }), 500

    ticker = resolve_symbol(ticker)

    stock, stock_data = get_yfinance_data(ticker)

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found or no data returned from yfinance.",
            "ticker": ticker
        }), 404

    stock_data = add_model_features(stock_data)
    latest_row = get_latest_valid_row(stock_data)

    if latest_row is None:
        return jsonify({
            "error": "Not enough recent data to calculate features.",
            "ticker": ticker
        }), 400

    return jsonify({
        "ticker": ticker,
        "company_name": get_company_name(stock),
        "latest_date": latest_row["Date"].strftime("%Y-%m-%d"),
        "current_price": format_price(latest_row["Close"]),
        "open": format_price(latest_row["Open"]),
        "high": format_price(latest_row["High"]),
        "low": format_price(latest_row["Low"]),
        "volume": safe_int(latest_row["Volume"]),
        "daily_return_percent": format_percent(latest_row["Daily_Return"]),
        "moving_average_5": format_price(latest_row["MA_5"]),
        "moving_average_10": format_price(latest_row["MA_10"]),
        "volume_change_percent": format_percent(latest_row["Volume_Change"]),
        "volatility_5": format_price(latest_row["Volatility_5"]),
        "data_source": "Yahoo Finance via yfinance",
        "note": "Prices are pulled from yfinance and may be delayed."
    })


@app.route("/history/<ticker>")
def get_history(ticker):
    ticker = resolve_symbol(ticker)
    rows = request.args.get("rows", default=60, type=int)

    stock, stock_data = get_yfinance_data(ticker, period="1y")

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found or no data returned from yfinance.",
            "ticker": ticker
        }), 404

    history = history_to_json(stock_data, rows=max(5, min(rows, 252)))

    return jsonify({
        "ticker": ticker,
        "count": len(history),
        "history": history,
        "data_source": "Yahoo Finance via yfinance",
        "note": "Historical prices are pulled from yfinance and may be delayed."
    })


@app.route("/forecast/<ticker>")
def forecast(ticker):
    days = request.args.get("days", default=10, type=int)
    data, error, status = build_forecast(ticker, days)

    if error:
        return jsonify(error), status

    return jsonify(data)


@app.route("/predict/<ticker>")
def predict(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Model files are not loaded correctly."
        }), 500

    ticker = resolve_symbol(ticker)

    stock, stock_data = get_yfinance_data(ticker)

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found or no data returned from yfinance.",
            "ticker": ticker
        }), 404

    stock_data = add_model_features(stock_data)
    latest_row = get_latest_valid_row(stock_data)

    if latest_row is None:
        return jsonify({
            "error": "Not enough recent data to make a prediction.",
            "ticker": ticker
        }), 400

    X_latest = latest_row[features].to_frame().T

    prediction_number = model.predict(X_latest)[0]
    prediction_proba = model.predict_proba(X_latest)[0]

    confidence = round(float(max(prediction_proba)) * 100, 2)

    prediction = "Up" if prediction_number == 1 else "Down"
    calibrated_prediction = prediction
    if confidence < 55:
        calibrated_prediction = "Uncertain"

    risk_level, risk_explanation = calculate_risk_level(
        confidence,
        latest_row["Volatility_5"]
    )

    forecast_data, _, _ = build_forecast(ticker, days=10)

    return jsonify({
        "ticker": ticker,
        "company_name": get_company_name(stock),
        "latest_date": latest_row["Date"].strftime("%Y-%m-%d"),
        "current_price": format_price(latest_row["Close"]),
        "open": format_price(latest_row["Open"]),
        "high": format_price(latest_row["High"]),
        "low": format_price(latest_row["Low"]),
        "volume": safe_int(latest_row["Volume"]),
        "daily_return_percent": format_percent(latest_row["Daily_Return"]),
        "moving_average_5": format_price(latest_row["MA_5"]),
        "moving_average_10": format_price(latest_row["MA_10"]),
        "volume_change_percent": format_percent(latest_row["Volume_Change"]),
        "volatility_5": format_price(latest_row["Volatility_5"]),
        "prediction": calibrated_prediction,
        "raw_model_prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "risk_explanation": risk_explanation,
        "forecast_summary": {
            "model": forecast_data["forecast_model"] if forecast_data else None,
            "days": forecast_data["forecast_days"] if forecast_data else None,
            "expected_change_percent": forecast_data["expected_change_percent"] if forecast_data else None
        },
        "explanation": "This prediction uses recent Yahoo Finance price data, the trained Random Forest direction model, and a separate time-series forecast for future price estimates.",
        "features_used": features,
        "data_source": "Yahoo Finance via yfinance",
        "note": "For educational use only. Not financial advice. Prices may be delayed."
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

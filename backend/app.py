from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import yfinance as yf
from pathlib import Path


app = Flask(__name__)
CORS(app)


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "stock_direction_model.pkl"
FEATURES_PATH = BASE_DIR / "models" / "features.pkl"


try:
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
except Exception as e:
    print("Error loading model files:", e)
    model = None
    features = None


def backend_ready():
    return model is not None and features is not None


def format_price(value):
    if pd.isna(value):
        return None
    return round(float(value), 2)


def format_percent(value):
    if pd.isna(value):
        return None
    return round(float(value) * 100, 2)


def calculate_risk_level(confidence, volatility):
    if volatility is None or pd.isna(volatility):
        return "Medium", "Risk is estimated as medium because volatility data is limited."

    if confidence >= 75 and volatility < 3:
        return "Low", "The model has higher confidence and recent volatility is relatively low."
    elif confidence >= 60 and volatility < 6:
        return "Medium", "The model has moderate confidence or the stock has some recent volatility."
    else:
        return "High", "The model has lower confidence or the stock has higher recent volatility."


def get_yfinance_data(ticker):
    ticker = ticker.upper().strip()

    stock = yf.Ticker(ticker)

    history = stock.history(period="60d", interval="1d")

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


def get_company_name(stock):
    try:
        info = stock.info
        return info.get("longName") or info.get("shortName") or "Company name unavailable"
    except Exception:
        return "Company name unavailable"


def get_latest_valid_row(stock_data):
    clean_data = stock_data.dropna(subset=features)

    if clean_data.empty:
        return None

    return clean_data.iloc[-1]


@app.route("/")
def home():
    return jsonify({
        "app": "StockSensei Backend",
        "status": "running",
        "data_source": "Yahoo Finance through yfinance",
        "routes": [
            "/health",
            "/live/<ticker>",
            "/history/<ticker>",
            "/predict/<ticker>"
        ],
        "note": "For educational use only. Not financial advice."
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok" if backend_ready() else "error",
        "model_loaded": model is not None,
        "features_loaded": features is not None,
        "data_source": "yfinance"
    })


@app.route("/live/<ticker>")
def live_summary(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Model files are not loaded correctly."
        }), 500

    ticker = ticker.upper().strip()

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

    company_name = get_company_name(stock)

    return jsonify({
        "ticker": ticker,
        "company_name": company_name,
        "latest_date": latest_row["Date"].strftime("%Y-%m-%d"),
        "current_price": format_price(latest_row["Close"]),
        "open": format_price(latest_row["Open"]),
        "high": format_price(latest_row["High"]),
        "low": format_price(latest_row["Low"]),
        "volume": int(latest_row["Volume"]),
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
    ticker = ticker.upper().strip()

    stock, stock_data = get_yfinance_data(ticker)

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found or no data returned from yfinance.",
            "ticker": ticker
        }), 404

    stock_data = stock_data.sort_values("Date").tail(30)

    history = []

    for _, row in stock_data.iterrows():
        history.append({
            "date": row["Date"].strftime("%Y-%m-%d"),
            "open": format_price(row["Open"]),
            "high": format_price(row["High"]),
            "low": format_price(row["Low"]),
            "close": format_price(row["Close"]),
            "volume": int(row["Volume"])
        })

    return jsonify({
        "ticker": ticker,
        "count": len(history),
        "history": history,
        "data_source": "Yahoo Finance via yfinance",
        "note": "Historical prices are pulled from yfinance and may be delayed."
    })


@app.route("/predict/<ticker>")
def predict(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Model files are not loaded correctly."
        }), 500

    ticker = ticker.upper().strip()

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

    risk_level, risk_explanation = calculate_risk_level(
        confidence,
        latest_row["Volatility_5"]
    )

    company_name = get_company_name(stock)

    return jsonify({
        "ticker": ticker,
        "company_name": company_name,
        "latest_date": latest_row["Date"].strftime("%Y-%m-%d"),
        "current_price": format_price(latest_row["Close"]),
        "open": format_price(latest_row["Open"]),
        "high": format_price(latest_row["High"]),
        "low": format_price(latest_row["Low"]),
        "volume": int(latest_row["Volume"]),
        "daily_return_percent": format_percent(latest_row["Daily_Return"]),
        "moving_average_5": format_price(latest_row["MA_5"]),
        "moving_average_10": format_price(latest_row["MA_10"]),
        "volume_change_percent": format_percent(latest_row["Volume_Change"]),
        "volatility_5": format_price(latest_row["Volatility_5"]),
        "prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "risk_explanation": risk_explanation,
        "explanation": "This prediction uses recent Yahoo Finance price data and the trained Random Forest stock direction model.",
        "features_used": features,
        "data_source": "Yahoo Finance via yfinance",
        "note": "For educational use only. Not financial advice. Prices may be delayed."
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
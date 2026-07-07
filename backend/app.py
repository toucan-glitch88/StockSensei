from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
from pathlib import Path


# -----------------------------
# App setup
# -----------------------------

app = Flask(__name__)
CORS(app)


# -----------------------------
# File paths
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "SP500_Historical_Data.csv"
MODEL_PATH = BASE_DIR / "models" / "stock_direction_model.pkl"
FEATURES_PATH = BASE_DIR / "models" / "features.pkl"


# -----------------------------
# Load data and model once
# -----------------------------

try:
    df = pd.read_csv(DATA_PATH)
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)

    df["Date"] = pd.to_datetime(df["Date"])

    # Make sure ticker symbols are uppercase
    df["Ticker"] = df["Ticker"].astype(str).str.upper()

    # Feature engineering
    df = df.sort_values(["Ticker", "Date"])

    df["Daily_Return"] = df.groupby("Ticker")["Close"].pct_change()
    df["MA_5"] = df.groupby("Ticker")["Close"].transform(
        lambda x: x.rolling(window=5).mean()
    )
    df["MA_10"] = df.groupby("Ticker")["Close"].transform(
        lambda x: x.rolling(window=10).mean()
    )
    df["Volume_Change"] = df.groupby("Ticker")["Volume"].pct_change()
    df["Volatility_5"] = df.groupby("Ticker")["Close"].transform(
        lambda x: x.rolling(window=5).std()
    )

except Exception as e:
    print("Error loading backend files:", e)
    df = None
    model = None
    features = None


# -----------------------------
# Helper functions
# -----------------------------

def backend_ready():
    return df is not None and model is not None and features is not None


def get_stock_data(ticker):
    ticker = ticker.upper()
    stock_data = df[df["Ticker"] == ticker].copy()

    if stock_data.empty:
        return None

    stock_data = stock_data.sort_values("Date")
    return stock_data


def get_latest_valid_row(stock_data):
    clean_data = stock_data.dropna(subset=features)

    if clean_data.empty:
        return None

    return clean_data.iloc[-1]


def calculate_risk_level(confidence, volatility):
    if volatility is None or pd.isna(volatility):
        return "Medium", "Risk is estimated as medium because volatility data is limited."

    if confidence >= 75 and volatility < 3:
        return "Low", "The model has higher confidence and recent volatility is relatively low."
    elif confidence >= 60 and volatility < 6:
        return "Medium", "The model has moderate confidence or the stock has some recent volatility."
    else:
        return "High", "The model has lower confidence or the stock has higher recent volatility."


def format_price(value):
    if pd.isna(value):
        return None
    return round(float(value), 2)


def format_percent(value):
    if pd.isna(value):
        return None
    return round(float(value) * 100, 2)


# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return jsonify({
        "app": "StockSensei Backend",
        "status": "running",
        "routes": [
            "/health",
            "/tickers",
            "/summary/<ticker>",
            "/history/<ticker>",
            "/predict/<ticker>"
        ],
        "note": "For educational use only. Not financial advice."
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok" if backend_ready() else "error",
        "data_loaded": df is not None,
        "model_loaded": model is not None,
        "features_loaded": features is not None
    })


@app.route("/tickers")
def get_tickers():
    if not backend_ready():
        return jsonify({
            "error": "Backend files are not loaded correctly."
        }), 500

    tickers = sorted(df["Ticker"].dropna().unique().tolist())

    return jsonify({
        "count": len(tickers),
        "tickers": tickers
    })


@app.route("/summary/<ticker>")
def get_summary(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Backend files are not loaded correctly."
        }), 500

    ticker = ticker.upper()
    stock_data = get_stock_data(ticker)

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found",
            "ticker": ticker
        }), 404

    latest_row = get_latest_valid_row(stock_data)

    if latest_row is None:
        return jsonify({
            "error": "Not enough clean data for this ticker",
            "ticker": ticker
        }), 400

    return jsonify({
        "ticker": ticker,
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
        "note": "Summary is based on the local historical dataset, not live market data."
    })


@app.route("/history/<ticker>")
def get_history(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Backend files are not loaded correctly."
        }), 500

    ticker = ticker.upper()
    stock_data = get_stock_data(ticker)

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found",
            "ticker": ticker
        }), 404

    recent_data = stock_data.tail(30)

    history = []

    for _, row in recent_data.iterrows():
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
        "note": "Historical data comes from the local dataset, not live market data."
    })


@app.route("/predict/<ticker>")
def predict(ticker):
    if not backend_ready():
        return jsonify({
            "error": "Backend files are not loaded correctly."
        }), 500

    ticker = ticker.upper()
    stock_data = get_stock_data(ticker)

    if stock_data is None:
        return jsonify({
            "error": "Ticker not found",
            "ticker": ticker
        }), 404

    latest_row = get_latest_valid_row(stock_data)

    if latest_row is None:
        return jsonify({
            "error": "Not enough clean data to make a prediction",
            "ticker": ticker
        }), 400

    X_latest = latest_row[features].to_frame().T

    prediction_number = model.predict(X_latest)[0]
    prediction_proba = model.predict_proba(X_latest)[0]

    confidence = round(float(max(prediction_proba)) * 100, 2)

    if prediction_number == 1:
        prediction = "Up"
    else:
        prediction = "Down"

    risk_level, risk_explanation = calculate_risk_level(
        confidence,
        latest_row["Volatility_5"]
    )

    return jsonify({
        "ticker": ticker,
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
        "explanation": "This prediction is based on recent price movement, moving averages, volume change, and volatility.",
        "features_used": features,
        "note": "For educational use only. Not financial advice."
    })


# -----------------------------
# Run app
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
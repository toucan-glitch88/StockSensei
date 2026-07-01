from flask import Flask, jsonify
import pandas as pd
import joblib

app = Flask(__name__)

model = joblib.load("backend/models/stock_direction_model.pkl")
features = joblib.load("backend/models/features.pkl")
df = pd.read_csv("backend/data/SP500_Historical_Data.csv")


@app.route("/")
def home():
    return jsonify({
        "message": "StockSensei backend is running"
    })


@app.route("/predict/<ticker>")
def predict(ticker):
    ticker = ticker.upper()

    stock = df[df["Ticker"] == ticker].copy()

    if stock.empty:
        return jsonify({
            "error": "Ticker not found"
        }), 404

    stock["Date"] = pd.to_datetime(stock["Date"])
    stock = stock.sort_values("Date")

    stock["Daily_Return"] = stock["Close"].pct_change()
    stock["MA_5"] = stock["Close"].rolling(5).mean()
    stock["MA_10"] = stock["Close"].rolling(10).mean()
    stock["Volume_Change"] = stock["Volume"].pct_change()
    stock["Volatility_5"] = stock["Daily_Return"].rolling(5).std()

    stock = stock.dropna()

    if stock.empty:
        return jsonify({
            "error": "Not enough data for this ticker"
        }), 400

    latest_data = stock[features].iloc[[-1]]

    prediction = model.predict(latest_data)[0]
    confidence = model.predict_proba(latest_data)[0].max()

    result = "Up" if prediction == 1 else "Down"

    return jsonify({
        "ticker": ticker,
        "prediction": result,
        "confidence": round(confidence * 100, 2),
        "explanation": "This prediction is based on recent price movement, moving averages, volume change, and volatility.",
        "features_used": [
            "Open price",
            "High price",
            "Low price",
            "Close price",
            "Volume",
            "Daily return",
            "5-day moving average",
            "10-day moving average",
            "Volume change",
            "5-day volatility"
        ],
        "note": "For educational use only. Not financial advice."
    })


if __name__ == "__main__":
    app.run(debug=True)
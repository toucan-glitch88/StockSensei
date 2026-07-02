from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import joblib

app = Flask(__name__)
CORS(app)

# Load saved model, features, and dataset
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

    # Get data for selected stock
    stock = df[df["Ticker"] == ticker].copy()

    if stock.empty:
        return jsonify({
            "error": "Ticker not found"
        }), 404

    # Sort by date
    stock["Date"] = pd.to_datetime(stock["Date"])
    stock = stock.sort_values("Date")

    # Create features
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

    # Latest row
    latest_row = stock.iloc[-1]
    latest_data = stock[features].iloc[[-1]]

    latest_date = latest_row["Date"].strftime("%Y-%m-%d")
    current_price = round(float(latest_row["Close"]), 2)
    daily_return = round(float(latest_row["Daily_Return"] * 100), 2)
    ma_5 = round(float(latest_row["MA_5"]), 2)
    ma_10 = round(float(latest_row["MA_10"]), 2)

    # Prediction
    prediction = model.predict(latest_data)[0]
    confidence = model.predict_proba(latest_data)[0].max()

    result = "Up" if prediction == 1 else "Down"

    # Risk level based on recent volatility
    latest_volatility = stock["Volatility_5"].iloc[-1]

    if latest_volatility >= 0.03:
        risk_level = "High"
        risk_explanation = "This stock has high recent volatility, meaning its price has been moving more sharply."
    elif latest_volatility >= 0.015:
        risk_level = "Medium"
        risk_explanation = "This stock has moderate recent volatility."
    else:
        risk_level = "Low"
        risk_explanation = "This stock has low recent volatility, meaning its recent price movement has been more stable."

    return jsonify({
        "ticker": ticker,
        "latest_date": latest_date,
        "current_price": current_price,
        "daily_return_percent": daily_return,
        "moving_average_5": ma_5,
        "moving_average_10": ma_10,
        "prediction": result,
        "confidence": round(confidence * 100, 2),
        "risk_level": risk_level,
        "risk_explanation": risk_explanation,
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
    app.run(debug=True, port=5000)
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "message": "StockSensei backend is running"
    })

@app.route("/predict/<ticker>")
def predict(ticker):
    return jsonify({
        "ticker": ticker.upper(),
        "prediction": "Down",
        "confidence": 83,
        "note": "This is a test API response. Not financial advice."
    })

if __name__ == "__main__":
    app.run(debug=True)